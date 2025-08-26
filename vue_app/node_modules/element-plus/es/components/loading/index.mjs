import Loading from './src/service.mjs';
export { default as ElLoadingService } from './src/service.mjs';
import vLoading from './src/directive.mjs';
export { default as ElLoadingDirective, default as vLoading } from './src/directive.mjs';

const ElLoading = {
  install(app) {
    Loading._context = app._context;
    vLoading._context = app._context;
    app.directive("loading", vLoading);
    app.config.globalProperties.$loading = Loading;
  },
  directive: vLoading,
  service: Loading
};

export { ElLoading, ElLoading as default };
//# sourceMappingURL=index.mjs.map
