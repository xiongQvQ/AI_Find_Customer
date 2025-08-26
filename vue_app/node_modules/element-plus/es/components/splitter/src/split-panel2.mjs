import { defineComponent, inject, toRefs, ref, getCurrentInstance, computed, watch, nextTick, reactive, onBeforeUnmount, openBlock, createElementBlock, Fragment, createElementVNode, mergeProps, unref, renderSlot, createBlock, withCtx, createCommentVNode } from 'vue';
import { isCollapsible, getCollapsible } from './hooks/usePanel.mjs';
import SplitBar from './split-bar.mjs';
import { splitterPanelProps } from './split-panel.mjs';
import { splitterRootContextKey } from './type.mjs';
import _export_sfc from '../../../_virtual/plugin-vue_export-helper.mjs';
import { isPct, getPct, isPx, getPx } from './hooks/useSize.mjs';
import { useNamespace } from '../../../hooks/use-namespace/index.mjs';
import { throwError } from '../../../utils/error.mjs';

const COMPONENT_NAME = "ElSplitterPanel";
const __default__ = defineComponent({
  name: COMPONENT_NAME
});
const _sfc_main = /* @__PURE__ */ defineComponent({
  ...__default__,
  props: splitterPanelProps,
  emits: ["update:size"],
  setup(__props, { emit: emits }) {
    const props = __props;
    const ns = useNamespace("splitter-panel");
    const splitterContext = inject(splitterRootContextKey);
    if (!splitterContext)
      throwError(COMPONENT_NAME, "usage: <el-splitter><el-splitter-panel /></el-splitter/>");
    const { panels, layout, lazy, containerSize, pxSizes } = toRefs(splitterContext);
    const {
      registerPanel,
      unregisterPanel,
      onCollapse,
      onMoveEnd,
      onMoveStart,
      onMoving
    } = splitterContext;
    const panelEl = ref();
    const instance = getCurrentInstance();
    const uid = instance.uid;
    const index = ref(0);
    const panel = computed(() => panels.value[index.value]);
    const setIndex = (val) => {
      index.value = val;
    };
    const panelSize = computed(() => {
      var _a;
      if (!panel.value)
        return 0;
      return (_a = pxSizes.value[index.value]) != null ? _a : 0;
    });
    const nextSize = computed(() => {
      var _a;
      if (!panel.value)
        return 0;
      return (_a = pxSizes.value[index.value + 1]) != null ? _a : 0;
    });
    const nextPanel = computed(() => {
      if (panel.value) {
        return panels.value[index.value + 1];
      }
      return null;
    });
    const isResizable = computed(() => {
      var _a;
      if (!nextPanel.value)
        return false;
      return props.resizable && ((_a = nextPanel.value) == null ? void 0 : _a.resizable) && (panelSize.value !== 0 || !props.min) && (nextSize.value !== 0 || !nextPanel.value.min);
    });
    const isShowBar = computed(() => {
      if (!panel.value)
        return false;
      return index.value !== panels.value.length - 1;
    });
    const startCollapsible = computed(() => isCollapsible(panel.value, panelSize.value, nextPanel.value, nextSize.value));
    const endCollapsible = computed(() => isCollapsible(nextPanel.value, nextSize.value, panel.value, panelSize.value));
    function sizeToPx(str) {
      if (isPct(str)) {
        return getPct(str) * containerSize.value || 0;
      } else if (isPx(str)) {
        return getPx(str);
      }
      return str != null ? str : 0;
    }
    let isSizeUpdating = false;
    watch(() => props.size, () => {
      if (!isSizeUpdating && panel.value) {
        const size = sizeToPx(props.size);
        const maxSize = sizeToPx(props.max);
        const minSize = sizeToPx(props.min);
        const finalSize = Math.min(Math.max(size, minSize || 0), maxSize || size);
        if (finalSize !== size) {
          emits("update:size", finalSize);
        }
        panel.value.size = finalSize;
      }
    });
    watch(() => {
      var _a;
      return (_a = panel.value) == null ? void 0 : _a.size;
    }, (val) => {
      if (val !== props.size) {
        isSizeUpdating = true;
        emits("update:size", val);
        nextTick(() => isSizeUpdating = false);
      }
    });
    watch(() => props.resizable, (val) => {
      if (panel.value) {
        panel.value.resizable = val;
      }
    });
    const _panel = reactive({
      el: panelEl.value,
      uid,
      getVnode: () => instance.vnode,
      setIndex,
      ...props,
      collapsible: computed(() => getCollapsible(props.collapsible))
    });
    registerPanel(_panel);
    onBeforeUnmount(() => unregisterPanel(_panel));
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock(Fragment, null, [
        createElementVNode("div", mergeProps({
          ref_key: "panelEl",
          ref: panelEl,
          class: [unref(ns).b()],
          style: { flexBasis: `${unref(panelSize)}px` }
        }, _ctx.$attrs), [
          renderSlot(_ctx.$slots, "default")
        ], 16),
        unref(isShowBar) ? (openBlock(), createBlock(SplitBar, {
          key: 0,
          index: index.value,
          layout: unref(layout),
          lazy: unref(lazy),
          resizable: unref(isResizable),
          "start-collapsible": unref(startCollapsible),
          "end-collapsible": unref(endCollapsible),
          onMoveStart: unref(onMoveStart),
          onMoving: unref(onMoving),
          onMoveEnd: unref(onMoveEnd),
          onCollapse: unref(onCollapse)
        }, {
          "start-collapsible": withCtx(() => [
            renderSlot(_ctx.$slots, "start-collapsible")
          ]),
          "end-collapsible": withCtx(() => [
            renderSlot(_ctx.$slots, "end-collapsible")
          ]),
          _: 3
        }, 8, ["index", "layout", "lazy", "resizable", "start-collapsible", "end-collapsible", "onMoveStart", "onMoving", "onMoveEnd", "onCollapse"])) : createCommentVNode("v-if", true)
      ], 64);
    };
  }
});
var SplitPanel = /* @__PURE__ */ _export_sfc(_sfc_main, [["__file", "split-panel.vue"]]);

export { SplitPanel as default };
//# sourceMappingURL=split-panel2.mjs.map
