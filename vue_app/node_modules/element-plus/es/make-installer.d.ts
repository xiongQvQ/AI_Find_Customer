import type { App, Plugin } from 'vue';
import type { ConfigProviderContext } from 'element-plus/es/components/config-provider';
export declare const makeInstaller: (components?: Plugin[]) => {
    version: string;
    install: (app: App, options?: ConfigProviderContext) => void;
};
