import ColorPickerPanel from './src/color-picker-panel2.mjs';
export { ROOT_COMMON_COLOR_INJECTION_KEY, colorPickerPanelContextKey, colorPickerPanelEmits, colorPickerPanelProps } from './src/color-picker-panel.mjs';
import { withInstall } from '../../utils/vue/install.mjs';

const ElColorPickerPanel = withInstall(ColorPickerPanel);

export { ElColorPickerPanel, ElColorPickerPanel as default };
//# sourceMappingURL=index.mjs.map
