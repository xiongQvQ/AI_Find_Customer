import Splitter from './src/splitter2.mjs';
import SplitPanel from './src/split-panel2.mjs';
export { splitterProps } from './src/splitter.mjs';
export { splitterPanelProps } from './src/split-panel.mjs';
import { withInstall, withNoopInstall } from '../../utils/vue/install.mjs';

const ElSplitter = withInstall(Splitter, {
  SplitPanel
});
const ElSplitterPanel = withNoopInstall(SplitPanel);

export { ElSplitter, ElSplitterPanel, ElSplitter as default };
//# sourceMappingURL=index.mjs.map
