import Loading from './src/service';
import vLoading from './src/directive';
import type { App, AppContext, Directive } from 'vue';
import type { ElementLoading, LoadingBinding } from './src/directive';
export declare const ElLoading: {
    install(app: App): void;
    directive: Directive<ElementLoading, LoadingBinding>;
    service: {
        (options?: import("./src/types").LoadingOptions): import("./src/loading").LoadingInstance;
        _context: AppContext | null;
    };
};
export default ElLoading;
export { vLoading, vLoading as ElLoadingDirective, Loading as ElLoadingService };
export * from './src/types';
