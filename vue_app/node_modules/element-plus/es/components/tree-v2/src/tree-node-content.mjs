import { defineComponent, inject, h } from 'vue';
import { ElText } from '../../text/index.mjs';
import { treeNodeContentProps, ROOT_TREE_INJECTION_KEY } from './virtual-tree.mjs';
import { useNamespace } from '../../../hooks/use-namespace/index.mjs';

var ElNodeContent = defineComponent({
  name: "ElTreeNodeContent",
  props: treeNodeContentProps,
  setup(props) {
    const tree = inject(ROOT_TREE_INJECTION_KEY);
    const ns = useNamespace("tree");
    return () => {
      const node = props.node;
      const { data } = node;
      return (tree == null ? void 0 : tree.ctx.slots.default) ? tree.ctx.slots.default({ node, data }) : h(ElText, { tag: "span", truncated: true, class: ns.be("node", "label") }, () => [node == null ? void 0 : node.label]);
    };
  }
});

export { ElNodeContent as default };
//# sourceMappingURL=tree-node-content.mjs.map
