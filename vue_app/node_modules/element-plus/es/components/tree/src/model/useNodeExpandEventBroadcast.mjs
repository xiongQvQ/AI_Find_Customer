import { inject, provide } from 'vue';
import { TREE_NODE_MAP_INJECTION_KEY } from '../tokens.mjs';

function useNodeExpandEventBroadcast(props) {
  const parentNodeMap = inject(TREE_NODE_MAP_INJECTION_KEY, null);
  const currentNodeMap = {
    treeNodeExpand: (node) => {
      var _a;
      if (props.node !== node) {
        (_a = props.node) == null ? void 0 : _a.collapse();
      }
    },
    children: []
  };
  if (parentNodeMap) {
    parentNodeMap.children.push(currentNodeMap);
  }
  provide(TREE_NODE_MAP_INJECTION_KEY, currentNodeMap);
  return {
    broadcastExpanded: (node) => {
      if (!props.accordion)
        return;
      for (const childNode of currentNodeMap.children) {
        childNode.treeNodeExpand(node);
      }
    }
  };
}

export { useNodeExpandEventBroadcast };
//# sourceMappingURL=useNodeExpandEventBroadcast.mjs.map
