import { defineComponent, ref, computed, watch, nextTick, provide, reactive, onActivated, onMounted, onUpdated, openBlock, createElementBlock, normalizeClass, unref, createElementVNode, normalizeStyle, createBlock, resolveDynamicComponent, withCtx, renderSlot, createCommentVNode } from 'vue';
import { useResizeObserver, useEventListener } from '@vueuse/core';
import Bar from './bar2.mjs';
import { scrollbarContextKey } from './constants.mjs';
import { scrollbarProps, scrollbarEmits } from './scrollbar.mjs';
import _export_sfc from '../../../_virtual/plugin-vue_export-helper.mjs';
import { useNamespace } from '../../../hooks/use-namespace/index.mjs';
import { addUnit } from '../../../utils/dom/style.mjs';
import { isObject } from '@vue/shared';
import { isNumber } from '../../../utils/types.mjs';

const COMPONENT_NAME = "ElScrollbar";
const __default__ = defineComponent({
  name: COMPONENT_NAME
});
const _sfc_main = /* @__PURE__ */ defineComponent({
  ...__default__,
  props: scrollbarProps,
  emits: scrollbarEmits,
  setup(__props, { expose, emit }) {
    const props = __props;
    const ns = useNamespace("scrollbar");
    let stopResizeObserver = void 0;
    let stopWrapResizeObserver = void 0;
    let stopResizeListener = void 0;
    let wrapScrollTop = 0;
    let wrapScrollLeft = 0;
    let direction = "";
    const distanceScrollState = {
      bottom: false,
      top: false,
      right: false,
      left: false
    };
    const scrollbarRef = ref();
    const wrapRef = ref();
    const resizeRef = ref();
    const barRef = ref();
    const wrapStyle = computed(() => {
      const style = {};
      if (props.height)
        style.height = addUnit(props.height);
      if (props.maxHeight)
        style.maxHeight = addUnit(props.maxHeight);
      return [props.wrapStyle, style];
    });
    const wrapKls = computed(() => {
      return [
        props.wrapClass,
        ns.e("wrap"),
        { [ns.em("wrap", "hidden-default")]: !props.native }
      ];
    });
    const resizeKls = computed(() => {
      return [ns.e("view"), props.viewClass];
    });
    const shouldSkipDirection = (direction2) => {
      var _a;
      return (_a = distanceScrollState[direction2]) != null ? _a : false;
    };
    const DIRECTION_PAIRS = {
      top: "bottom",
      bottom: "top",
      left: "right",
      right: "left"
    };
    const updateTriggerStatus = (arrivedStates) => {
      const oppositeDirection = DIRECTION_PAIRS[direction];
      if (!oppositeDirection)
        return;
      const arrived = arrivedStates[direction];
      const oppositeArrived = arrivedStates[oppositeDirection];
      if (arrived && !distanceScrollState[direction]) {
        distanceScrollState[direction] = true;
      }
      if (!oppositeArrived && distanceScrollState[oppositeDirection]) {
        distanceScrollState[oppositeDirection] = false;
      }
    };
    const handleScroll = () => {
      var _a;
      if (wrapRef.value) {
        (_a = barRef.value) == null ? void 0 : _a.handleScroll(wrapRef.value);
        const prevTop = wrapScrollTop;
        const prevLeft = wrapScrollLeft;
        wrapScrollTop = wrapRef.value.scrollTop;
        wrapScrollLeft = wrapRef.value.scrollLeft;
        const arrivedStates = {
          bottom: wrapScrollTop + wrapRef.value.clientHeight >= wrapRef.value.scrollHeight - props.distance,
          top: wrapScrollTop <= props.distance && prevTop !== 0,
          right: wrapScrollLeft + wrapRef.value.clientWidth >= wrapRef.value.scrollWidth - props.distance && prevLeft !== wrapScrollLeft,
          left: wrapScrollLeft <= props.distance && prevLeft !== 0
        };
        emit("scroll", {
          scrollTop: wrapScrollTop,
          scrollLeft: wrapScrollLeft
        });
        if (prevTop !== wrapScrollTop) {
          direction = wrapScrollTop > prevTop ? "bottom" : "top";
        }
        if (prevLeft !== wrapScrollLeft) {
          direction = wrapScrollLeft > prevLeft ? "right" : "left";
        }
        if (props.distance > 0) {
          if (shouldSkipDirection(direction)) {
            return;
          }
          updateTriggerStatus(arrivedStates);
        }
        if (arrivedStates[direction])
          emit("end-reached", direction);
      }
    };
    function scrollTo(arg1, arg2) {
      if (isObject(arg1)) {
        wrapRef.value.scrollTo(arg1);
      } else if (isNumber(arg1) && isNumber(arg2)) {
        wrapRef.value.scrollTo(arg1, arg2);
      }
    }
    const setScrollTop = (value) => {
      if (!isNumber(value)) {
        return;
      }
      wrapRef.value.scrollTop = value;
    };
    const setScrollLeft = (value) => {
      if (!isNumber(value)) {
        return;
      }
      wrapRef.value.scrollLeft = value;
    };
    const update = () => {
      var _a;
      (_a = barRef.value) == null ? void 0 : _a.update();
      distanceScrollState[direction] = false;
    };
    watch(() => props.noresize, (noresize) => {
      if (noresize) {
        stopResizeObserver == null ? void 0 : stopResizeObserver();
        stopWrapResizeObserver == null ? void 0 : stopWrapResizeObserver();
        stopResizeListener == null ? void 0 : stopResizeListener();
      } else {
        ({ stop: stopResizeObserver } = useResizeObserver(resizeRef, update));
        ({ stop: stopWrapResizeObserver } = useResizeObserver(wrapRef, update));
        stopResizeListener = useEventListener("resize", update);
      }
    }, { immediate: true });
    watch(() => [props.maxHeight, props.height], () => {
      if (!props.native)
        nextTick(() => {
          var _a;
          update();
          if (wrapRef.value) {
            (_a = barRef.value) == null ? void 0 : _a.handleScroll(wrapRef.value);
          }
        });
    });
    provide(scrollbarContextKey, reactive({
      scrollbarElement: scrollbarRef,
      wrapElement: wrapRef
    }));
    onActivated(() => {
      if (wrapRef.value) {
        wrapRef.value.scrollTop = wrapScrollTop;
        wrapRef.value.scrollLeft = wrapScrollLeft;
      }
    });
    onMounted(() => {
      if (!props.native)
        nextTick(() => {
          update();
        });
    });
    onUpdated(() => update());
    expose({
      wrapRef,
      update,
      scrollTo,
      setScrollTop,
      setScrollLeft,
      handleScroll
    });
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", {
        ref_key: "scrollbarRef",
        ref: scrollbarRef,
        class: normalizeClass(unref(ns).b())
      }, [
        createElementVNode("div", {
          ref_key: "wrapRef",
          ref: wrapRef,
          class: normalizeClass(unref(wrapKls)),
          style: normalizeStyle(unref(wrapStyle)),
          tabindex: _ctx.tabindex,
          onScroll: handleScroll
        }, [
          (openBlock(), createBlock(resolveDynamicComponent(_ctx.tag), {
            id: _ctx.id,
            ref_key: "resizeRef",
            ref: resizeRef,
            class: normalizeClass(unref(resizeKls)),
            style: normalizeStyle(_ctx.viewStyle),
            role: _ctx.role,
            "aria-label": _ctx.ariaLabel,
            "aria-orientation": _ctx.ariaOrientation
          }, {
            default: withCtx(() => [
              renderSlot(_ctx.$slots, "default")
            ]),
            _: 3
          }, 8, ["id", "class", "style", "role", "aria-label", "aria-orientation"]))
        ], 46, ["tabindex"]),
        !_ctx.native ? (openBlock(), createBlock(Bar, {
          key: 0,
          ref_key: "barRef",
          ref: barRef,
          always: _ctx.always,
          "min-size": _ctx.minSize
        }, null, 8, ["always", "min-size"])) : createCommentVNode("v-if", true)
      ], 2);
    };
  }
});
var Scrollbar = /* @__PURE__ */ _export_sfc(_sfc_main, [["__file", "scrollbar.vue"]]);

export { Scrollbar as default };
//# sourceMappingURL=scrollbar2.mjs.map
