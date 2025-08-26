import { shallowRef, triggerRef, onMounted, defineComponent, h, isVNode } from 'vue';
import { flattedChildren } from '../../utils/vue/vnode.mjs';

const getOrderedChildren = (vm, childComponentName, children) => {
  const nodes = flattedChildren(vm.subTree).filter((n) => {
    var _a;
    return isVNode(n) && ((_a = n.type) == null ? void 0 : _a.name) === childComponentName && !!n.component;
  });
  const uids = nodes.map((n) => n.component.uid);
  return uids.map((uid) => children[uid]).filter((p) => !!p);
};
const useOrderedChildren = (vm, childComponentName) => {
  const children = shallowRef({});
  const orderedChildren = shallowRef([]);
  const nodesMap = /* @__PURE__ */ new WeakMap();
  const addChild = (child) => {
    children.value[child.uid] = child;
    triggerRef(children);
    onMounted(() => {
      const childNode = child.getVnode().el;
      const parentNode = childNode.parentNode;
      if (!nodesMap.has(parentNode)) {
        nodesMap.set(parentNode, []);
        const originalFn = parentNode.insertBefore.bind(parentNode);
        parentNode.insertBefore = (node, anchor) => {
          const shouldSortChildren = nodesMap.get(parentNode).some((el) => node === el || anchor === el);
          if (shouldSortChildren)
            triggerRef(children);
          return originalFn(node, anchor);
        };
      }
      nodesMap.get(parentNode).push(childNode);
    });
  };
  const removeChild = (child) => {
    delete children.value[child.uid];
    triggerRef(children);
    const childNode = child.getVnode().el;
    const parentNode = childNode.parentNode;
    const childNodes = nodesMap.get(parentNode);
    const index = childNodes.indexOf(childNode);
    childNodes.splice(index, 1);
  };
  const sortChildren = () => {
    orderedChildren.value = getOrderedChildren(vm, childComponentName, children.value);
  };
  const IsolatedRenderer = (props) => {
    return props.render();
  };
  const ChildrenSorter = defineComponent({
    setup(_, { slots }) {
      return () => {
        sortChildren();
        return slots.default ? h(IsolatedRenderer, {
          render: slots.default
        }) : null;
      };
    }
  });
  return {
    children: orderedChildren,
    addChild,
    removeChild,
    ChildrenSorter
  };
};

export { useOrderedChildren };
//# sourceMappingURL=index.mjs.map
