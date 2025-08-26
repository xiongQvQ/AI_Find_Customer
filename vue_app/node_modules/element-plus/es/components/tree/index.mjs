import Tree from './src/tree.mjs';
export { NODE_INSTANCE_INJECTION_KEY, ROOT_TREE_INJECTION_KEY, TREE_NODE_MAP_INJECTION_KEY } from './src/tokens.mjs';
import { withInstall } from '../../utils/vue/install.mjs';

const ElTree = withInstall(Tree);

export { ElTree, ElTree as default };
//# sourceMappingURL=index.mjs.map
