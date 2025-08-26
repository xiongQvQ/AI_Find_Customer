import { defineComponent, computed, ref, openBlock, createElementBlock, normalizeClass, unref, normalizeStyle, renderSlot, createBlock, resolveDynamicComponent, createCommentVNode, createElementVNode } from 'vue';
import { ArrowLeft, ArrowUp, ArrowRight, ArrowDown } from '@element-plus/icons-vue';
import _export_sfc from '../../../_virtual/plugin-vue_export-helper.mjs';
import { useNamespace } from '../../../hooks/use-namespace/index.mjs';

const __default__ = defineComponent({
  name: "ElSplitterBar"
});
const _sfc_main = /* @__PURE__ */ defineComponent({
  ...__default__,
  props: {
    index: {
      type: Number,
      required: true
    },
    layout: {
      type: String,
      values: ["horizontal", "vertical"],
      default: "horizontal"
    },
    resizable: {
      type: Boolean,
      default: true
    },
    lazy: Boolean,
    startCollapsible: Boolean,
    endCollapsible: Boolean
  },
  emits: ["moveStart", "moving", "moveEnd", "collapse"],
  setup(__props, { emit }) {
    const props = __props;
    const ns = useNamespace("splitter-bar");
    const isHorizontal = computed(() => props.layout === "horizontal");
    const barWrapStyles = computed(() => {
      if (isHorizontal.value) {
        return { width: 0 };
      }
      return { height: 0 };
    });
    const draggerStyles = computed(() => {
      return {
        width: isHorizontal.value ? "16px" : "100%",
        height: isHorizontal.value ? "100%" : "16px",
        cursor: isHorizontal.value ? "col-resize" : "row-resize",
        touchAction: "none"
      };
    });
    const draggerPseudoClass = computed(() => {
      const prefix = ns.e("dragger");
      return {
        [`${prefix}-horizontal`]: isHorizontal.value,
        [`${prefix}-vertical`]: !isHorizontal.value,
        [`${prefix}-active`]: !!startPos.value
      };
    });
    const startPos = ref(null);
    const onMousedown = (e) => {
      if (!props.resizable)
        return;
      startPos.value = [e.pageX, e.pageY];
      emit("moveStart", props.index);
      window.addEventListener("mouseup", onMouseUp);
      window.addEventListener("mousemove", onMouseMove);
    };
    const onTouchStart = (e) => {
      if (props.resizable && e.touches.length === 1) {
        e.preventDefault();
        const touch = e.touches[0];
        startPos.value = [touch.pageX, touch.pageY];
        emit("moveStart", props.index);
        window.addEventListener("touchend", onTouchEnd);
        window.addEventListener("touchmove", onTouchMove);
      }
    };
    const onMouseMove = (e) => {
      const { pageX, pageY } = e;
      const offsetX = pageX - startPos.value[0];
      const offsetY = pageY - startPos.value[1];
      const offset = isHorizontal.value ? offsetX : offsetY;
      emit("moving", props.index, offset);
    };
    const onTouchMove = (e) => {
      if (e.touches.length === 1) {
        e.preventDefault();
        const touch = e.touches[0];
        const offsetX = touch.pageX - startPos.value[0];
        const offsetY = touch.pageY - startPos.value[1];
        const offset = isHorizontal.value ? offsetX : offsetY;
        emit("moving", props.index, offset);
      }
    };
    const onMouseUp = () => {
      startPos.value = null;
      window.removeEventListener("mouseup", onMouseUp);
      window.removeEventListener("mousemove", onMouseMove);
      emit("moveEnd", props.index);
    };
    const onTouchEnd = () => {
      startPos.value = null;
      window.removeEventListener("touchend", onTouchEnd);
      window.removeEventListener("touchmove", onTouchMove);
      emit("moveEnd", props.index);
    };
    const StartIcon = computed(() => isHorizontal.value ? ArrowLeft : ArrowUp);
    const EndIcon = computed(() => isHorizontal.value ? ArrowRight : ArrowDown);
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", {
        class: normalizeClass([unref(ns).b()]),
        style: normalizeStyle(unref(barWrapStyles))
      }, [
        __props.startCollapsible ? (openBlock(), createElementBlock("div", {
          key: 0,
          class: normalizeClass([unref(ns).e("collapse-icon"), unref(ns).e(`${__props.layout}-collapse-icon-start`)]),
          onClick: ($event) => emit("collapse", __props.index, "start")
        }, [
          renderSlot(_ctx.$slots, "start-collapsible", {}, () => [
            (openBlock(), createBlock(resolveDynamicComponent(unref(StartIcon)), { style: { "width": "12px", "height": "12px" } }))
          ])
        ], 10, ["onClick"])) : createCommentVNode("v-if", true),
        createElementVNode("div", {
          class: normalizeClass([
            unref(ns).e("dragger"),
            unref(draggerPseudoClass),
            __props.resizable ? "" : unref(ns).e("disable"),
            unref(ns).is("lazy", __props.resizable && __props.lazy)
          ]),
          style: normalizeStyle(unref(draggerStyles)),
          onMousedown,
          onTouchstart: onTouchStart
        }, null, 38),
        __props.endCollapsible ? (openBlock(), createElementBlock("div", {
          key: 1,
          class: normalizeClass([unref(ns).e("collapse-icon"), unref(ns).e(`${__props.layout}-collapse-icon-end`)]),
          onClick: ($event) => emit("collapse", __props.index, "end")
        }, [
          renderSlot(_ctx.$slots, "end-collapsible", {}, () => [
            (openBlock(), createBlock(resolveDynamicComponent(unref(EndIcon)), { style: { "width": "12px", "height": "12px" } }))
          ])
        ], 10, ["onClick"])) : createCommentVNode("v-if", true)
      ], 6);
    };
  }
});
var SplitBar = /* @__PURE__ */ _export_sfc(_sfc_main, [["__file", "split-bar.vue"]]);

export { SplitBar as default };
//# sourceMappingURL=split-bar.mjs.map
