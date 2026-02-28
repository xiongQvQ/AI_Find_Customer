// AI Hunter — Tauri main process
// Responsibilities:
//   1. Start the Python backend sidecar
//   2. Poll /health until the backend is ready, then show the main window
//   3. System tray: Show / Hide / Quit
//   4. Gracefully kill the sidecar on app exit

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::net::TcpStream;
use std::process::{Child, Command};
use std::sync::Mutex;
use std::thread;
use std::time::{Duration, Instant};
use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    AppHandle, Manager, State,
};

const BACKEND_PORT: u16 = 8000;
const HEALTH_URL: &str = "http://127.0.0.1:8000/api/v1/health";
/// How long to wait for the backend before giving up (seconds)
const STARTUP_TIMEOUT_SECS: u64 = 60;
/// Polling interval while waiting for backend
const POLL_INTERVAL_MS: u64 = 200;

// ── State ────────────────────────────────────────────────────────────────────

struct BackendProcess(Mutex<Option<Child>>);

// ── Backend lifecycle ────────────────────────────────────────────────────────

fn sidecar_path(app: &AppHandle) -> Result<std::path::PathBuf, String> {
    let exe_name = if cfg!(windows) { "AIHunter.exe" } else { "AIHunter" };
    // Resources are mapped as "../../dist/AIHunter/**/*" -> "resources/AIHunter"
    // so the binary lives at <resource_dir>/resources/AIHunter/AIHunter
    app.path()
        .resource_dir()
        .map_err(|e| e.to_string())
        .map(|p| p.join("resources").join("AIHunter").join(exe_name))
}

/// Return a writable path for the backend binary.
/// On macOS the .app may live inside a read-only DMG, so we copy the entire
/// AIHunter bundle to ~/Library/Caches/AIHunter on first run.
fn writable_backend_path(app: &AppHandle) -> Result<std::path::PathBuf, String> {
    let exe_name = if cfg!(windows) { "AIHunter.exe" } else { "AIHunter" };
    let src_dir = {
        app.path()
            .resource_dir()
            .map_err(|e| e.to_string())?
            .join("resources")
            .join("AIHunter")
    };

    // Destination: ~/Library/Caches/AIHunter  (always writable)
    let cache_dir = app
        .path()
        .cache_dir()
        .map_err(|e| e.to_string())?
        .join("AIHunter");

    let dest_bin = cache_dir.join(exe_name);

    // Copy only when the source is newer or the destination doesn't exist yet.
    let needs_copy = !dest_bin.exists() || {
        let src_meta = std::fs::metadata(src_dir.join(exe_name)).ok();
        let dst_meta = std::fs::metadata(&dest_bin).ok();
        match (src_meta, dst_meta) {
            (Some(s), Some(d)) => s.len() != d.len(),
            _ => true,
        }
    };

    if needs_copy {
        // Remove stale cache copy first
        if cache_dir.exists() {
            std::fs::remove_dir_all(&cache_dir)
                .map_err(|e| format!("Failed to clean cache dir: {e}"))?;
        }
        copy_dir_all(&src_dir, &cache_dir)
            .map_err(|e| format!("Failed to copy backend bundle: {e}"))?;
        println!("[Tauri] Backend bundle copied to {}", cache_dir.display());
    }

    // Ensure execute bit is set on the writable copy
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let mut perms = std::fs::metadata(&dest_bin)
            .map_err(|e| format!("Failed to read binary metadata: {e}"))?
            .permissions();
        perms.set_mode(perms.mode() | 0o111);
        std::fs::set_permissions(&dest_bin, perms)
            .map_err(|e| format!("Failed to chmod backend binary: {e}"))?;
    }

    Ok(dest_bin)
}

/// Recursively copy a directory tree from `src` to `dst`.
fn copy_dir_all(src: &std::path::Path, dst: &std::path::Path) -> std::io::Result<()> {
    std::fs::create_dir_all(dst)?;
    for entry in std::fs::read_dir(src)? {
        let entry = entry?;
        let ty = entry.file_type()?;
        let dest_path = dst.join(entry.file_name());
        if ty.is_dir() {
            copy_dir_all(&entry.path(), &dest_path)?;
        } else {
            std::fs::copy(entry.path(), &dest_path)?;
        }
    }
    Ok(())
}

fn start_backend(app: &AppHandle) -> Result<Child, String> {
    let path = writable_backend_path(app)?;
    Command::new(&path)
        .current_dir(path.parent().unwrap_or(&path))
        .spawn()
        .map_err(|e| format!("Failed to spawn backend: {e}"))
}

/// Block until the backend TCP port accepts connections or timeout is reached.
/// Returns true if backend is ready, false on timeout.
fn wait_for_backend(timeout_secs: u64) -> bool {
    let deadline = Instant::now() + Duration::from_secs(timeout_secs);
    while Instant::now() < deadline {
        if TcpStream::connect(("127.0.0.1", BACKEND_PORT)).is_ok() {
            return true;
        }
        thread::sleep(Duration::from_millis(POLL_INTERVAL_MS));
    }
    false
}

fn kill_backend(state: &State<BackendProcess>) {
    if let Some(mut child) = state.0.lock().unwrap().take() {
        let _ = child.kill();
        let _ = child.wait();
        println!("[Tauri] Backend process terminated");
    }
}

// ── Tauri commands ───────────────────────────────────────────────────────────

#[tauri::command]
fn get_backend_url() -> String {
    format!("http://127.0.0.1:{BACKEND_PORT}")
}

// ── Tray ─────────────────────────────────────────────────────────────────────

fn build_tray(app: &AppHandle) -> tauri::Result<()> {
    let show_item = MenuItem::with_id(app, "show", "Show AI Hunter", true, None::<&str>)?;
    let hide_item = MenuItem::with_id(app, "hide", "Hide", true, None::<&str>)?;
    let quit_item = MenuItem::with_id(app, "quit", "Quit", true, None::<&str>)?;
    let menu = Menu::with_items(app, &[&show_item, &hide_item, &quit_item])?;

    TrayIconBuilder::new()
        .icon(app.default_window_icon().unwrap().clone())
        .menu(&menu)
        .tooltip("AI Hunter")
        .on_menu_event(|app, event| match event.id.as_ref() {
            "show" => {
                if let Some(win) = app.get_webview_window("main") {
                    let _ = win.show();
                    let _ = win.set_focus();
                }
            }
            "hide" => {
                if let Some(win) = app.get_webview_window("main") {
                    let _ = win.hide();
                }
            }
            "quit" => {
                kill_backend(&app.state::<BackendProcess>());
                app.exit(0);
            }
            _ => {}
        })
        .on_tray_icon_event(|tray, event| {
            // Double-click tray icon to show window
            if let TrayIconEvent::Click {
                button: MouseButton::Left,
                button_state: MouseButtonState::Up,
                ..
            } = event
            {
                let app = tray.app_handle();
                if let Some(win) = app.get_webview_window("main") {
                    let _ = win.show();
                    let _ = win.set_focus();
                }
            }
        })
        .build(app)?;
    Ok(())
}

// ── Main ─────────────────────────────────────────────────────────────────────

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .manage(BackendProcess(Mutex::new(None)))
        .setup(|app| {
            let handle = app.handle().clone();

            // Build system tray
            build_tray(&handle)?;

            // Hide main window while backend is starting up
            if let Some(win) = handle.get_webview_window("main") {
                let _ = win.hide();
            }

            // In dev mode the backend is started separately; skip sidecar launch.
            #[cfg(dev)]
            {
                println!("[Tauri] Dev mode: assuming backend already running on port {BACKEND_PORT}");
                let handle2 = handle.clone();
                thread::spawn(move || {
                    if wait_for_backend(STARTUP_TIMEOUT_SECS) {
                        println!("[Tauri] Backend ready at {HEALTH_URL}");
                        if let Some(win) = handle2.get_webview_window("main") {
                            let _ = win.show();
                            let _ = win.set_focus();
                        }
                    } else {
                        eprintln!("[Tauri] Backend not reachable — showing window anyway");
                        if let Some(win) = handle2.get_webview_window("main") {
                            let _ = win.show();
                            let _ = win.set_focus();
                        }
                    }
                });
            }

            // In production, start the bundled sidecar.
            #[cfg(not(dev))]
            {
                let backend_state: State<BackendProcess> = app.state();
                match start_backend(&handle) {
                    Err(e) => {
                        eprintln!("[Tauri] Cannot start backend: {e}");
                        tauri::async_runtime::spawn(async move {
                            tauri_plugin_dialog::DialogExt::dialog(&handle)
                                .message(format!(
                                    "AI Hunter could not start the backend service.\n\n{e}"
                                ))
                                .title("Startup Error")
                                .blocking_show();
                            handle.exit(1);
                        });
                    }
                    Ok(child) => {
                        *backend_state.0.lock().unwrap() = Some(child);
                        println!("[Tauri] Backend process spawned, waiting for ready...");

                        let handle2 = handle.clone();
                        thread::spawn(move || {
                            if wait_for_backend(STARTUP_TIMEOUT_SECS) {
                                println!("[Tauri] Backend is ready at {HEALTH_URL}");
                                if let Some(win) = handle2.get_webview_window("main") {
                                    let _ = win.show();
                                    let _ = win.set_focus();
                                }
                            } else {
                                eprintln!("[Tauri] Backend failed to start within {STARTUP_TIMEOUT_SECS}s");
                                tauri::async_runtime::spawn(async move {
                                    tauri_plugin_dialog::DialogExt::dialog(&handle2)
                                        .message(
                                            "AI Hunter backend did not start within 60 seconds.\n\
                                             Please check that port 8000 is not in use and try again.",
                                        )
                                        .title("Startup Timeout")
                                        .blocking_show();
                                    handle2.exit(1);
                                });
                            }
                        });
                    }
                }
            }
            Ok(())
        })
        // Intercept close button — minimize to tray instead of quitting
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                api.prevent_close();
                let _ = window.hide();
            }
        })
        .invoke_handler(tauri::generate_handler![get_backend_url])
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app, event| {
            if let tauri::RunEvent::Exit = event {
                kill_backend(&app.state::<BackendProcess>());
            }
        });
}
