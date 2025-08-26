import { defineComponent, toRef, getCurrentInstance, watch, computed, provide, reactive, openBlock, createElementBlock, normalizeClass, unref, normalizeStyle, renderSlot, createVNode, createCommentVNode } from 'vue';
import { splitterProps } from './splitter.mjs';
import { splitterRootContextKey } from './type.mjs';
import _export_sfc from '../../../_virtual/plugin-vue_export-helper.mjs';
import { useContainer } from './hooks/useContainer.mjs';
import { useSize } from './hooks/useSize.mjs';
import { useResize } from './hooks/useResize.mjs';
import { useNamespace } from '../../../hooks/use-namespace/index.mjs';
import { useOrderedChildren } from '../../../hooks/use-ordered-children/index.mjs';

const __default__ = defineComponent({
  name: "ElSplitter"
});
const _sfc_main = /* @__PURE__ */ defineComponent({
  ...__default__,
  props: splitterProps,
  emits: ["resizeStart", "resize", "resizeEnd", "collapse"],
  setup(__props, { emit: emits }) {
    const props = __props;
    const ns = useNamespace("splitter");
    const layout = toRef(props, "layout");
    const lazy = toRef(props, "lazy");
    const { containerEl, containerSize } = useContainer(layout);
    const {
      removeChild: unregisterPanel,
      children: panels,
      addChild: registerPanel,
      ChildrenSorter: PanelsSorter
    } = useOrderedChildren(getCurrentInstance(), "ElSplitterPanel");
    watch(panels, () => {
      panels.value.forEach((instance, index) => {
        instance.setIndex(index);
      });
    });
    const { percentSizes, pxSizes } = useSize(panels, containerSize);
    const {
      lazyOffset,
      movingIndex,
      onMoveStart,
      onMoving,
      onMoveEnd,
      onCollapse
    } = useResize(panels, containerSize, pxSizes, lazy);
    const splitterStyles = computed(() => {
      return {
        [`--${ns.b()}-bar-offset`]: lazy.value ? `${lazyOffset.value}px` : void 0
      };
    });
    const onResizeStart = (index) => {
      onMoveStart(index);
      emits("resizeStart", index, pxSizes.value);
    };
    const onResize = (index, offset) => {
      onMoving(index, offset);
      if (!lazy.value) {
        emits("resize", index, pxSizes.value);
      }
    };
    const onResizeEnd = (index) => {
      onMoveEnd();
      emits("resizeEnd", index, pxSizes.value);
    };
    const onCollapsible = (index, type) => {
      onCollapse(index, type);
      emits("collapse", index, type, pxSizes.value);
    };
    provide(splitterRootContextKey, reactive({
      panels,
      percentSizes,
      pxSizes,
      layout,
      lazy,
      movingIndex,
      containerSize,
      onMoveStart: onResizeStart,
      onMoving: onResize,
      onMoveEnd: onResizeEnd,
      onCollapse: onCollapsible,
      registerPanel,
      unregisterPanel
    }));
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", {
        ref_key: "containerEl",
        ref: containerEl,
        class: normalizeClass([unref(ns).b(), unref(ns).e(unref(layout))]),
        style: normalizeStyle(unref(splitterStyles))
      }, [
        renderSlot(_ctx.$slots, "default"),
        createVNode(unref(PanelsSorter)),
        createCommentVNode(" Prevent iframe touch events from breaking "),
        unref(movingIndex) ? (openBlock(), createElementBlock("div", {
          key: 0,
          class: normalizeClass([unref(ns).e("mask"), unref(ns).e(`mask-${unref(layout)}`)])
        }, null, 2)) : createCommentVNode("v-if", true)
      ], 6);
    };
  }
});
var Splitter = /* @__PURE__ */ _export_sfc(_sfc_main, [["__file", "splitter.vue"]]);

export { Splitter as default };
//# sourceMappingURL=splitter2.mjs.map
