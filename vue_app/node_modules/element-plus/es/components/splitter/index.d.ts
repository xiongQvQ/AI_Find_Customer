import Splitter from './src/splitter.vue';
import SplitPanel from './src/split-panel.vue';
import type { SFCWithInstall } from 'element-plus/es/utils';
export declare const ElSplitter: SFCWithInstall<typeof Splitter> & {
    SplitPanel: typeof SplitPanel;
};
export default ElSplitter;
export declare const ElSplitterPanel: SFCWithInstall<typeof SplitPanel>;
export * from './src/splitter';
export * from './src/split-panel';
