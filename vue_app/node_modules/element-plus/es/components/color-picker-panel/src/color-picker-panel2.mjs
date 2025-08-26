import { defineComponent, ref, inject, onMounted, nextTick, watch, provide, computed, openBlock, createElementBlock, normalizeClass, unref, createElementVNode, createVNode, createBlock, createCommentVNode, renderSlot } from 'vue';
import { ElInput } from '../../input/index.mjs';
import AlphaSlider from './components/alpha-slider.mjs';
import HueSlider from './components/hue-slider.mjs';
import Predefine from './components/predefine.mjs';
import SvPanel from './components/sv-panel.mjs';
import { colorPickerPanelProps, colorPickerPanelEmits, ROOT_COMMON_COLOR_INJECTION_KEY, colorPickerPanelContextKey } from './color-picker-panel.mjs';
import { useCommonColor } from './composables/use-common-color.mjs';
import _export_sfc from '../../../_virtual/plugin-vue_export-helper.mjs';
import { useNamespace } from '../../../hooks/use-namespace/index.mjs';
import { useFormDisabled } from '../../form/src/hooks/use-form-common-props.mjs';
import { UPDATE_MODEL_EVENT } from '../../../constants/event.mjs';

const __default__ = defineComponent({
  name: "ElColorPickerPanel"
});
const _sfc_main = /* @__PURE__ */ defineComponent({
  ...__default__,
  props: colorPickerPanelProps,
  emits: colorPickerPanelEmits,
  setup(__props, { expose, emit }) {
    const props = __props;
    const ns = useNamespace("color-picker-panel");
    const disabled = useFormDisabled();
    const hue = ref();
    const sv = ref();
    const alpha = ref();
    const inputRef = ref();
    const customInput = ref("");
    const { color } = inject(ROOT_COMMON_COLOR_INJECTION_KEY, () => useCommonColor(props, emit), true);
    function handleConfirm() {
      color.fromString(customInput.value);
      if (color.value !== customInput.value) {
        customInput.value = color.value;
      }
    }
    onMounted(() => {
      if (props.modelValue) {
        customInput.value = color.value;
      }
      nextTick(() => {
        var _a, _b, _c;
        (_a = hue.value) == null ? void 0 : _a.update();
        (_b = sv.value) == null ? void 0 : _b.update();
        (_c = alpha.value) == null ? void 0 : _c.update();
      });
    });
    watch(() => props.modelValue, (newVal) => {
      if (newVal && newVal !== color.value) {
        color.fromString(newVal);
      }
    });
    watch(() => color.value, (val) => {
      emit(UPDATE_MODEL_EVENT, val);
      customInput.value = val;
    });
    provide(colorPickerPanelContextKey, {
      currentColor: computed(() => color.value)
    });
    expose({
      color,
      inputRef
    });
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", {
        class: normalizeClass([unref(ns).b(), unref(ns).is("disabled", unref(disabled)), unref(ns).is("border", _ctx.border)])
      }, [
        createElementVNode("div", {
          class: normalizeClass(unref(ns).e("wrapper"))
        }, [
          createVNode(HueSlider, {
            ref_key: "hue",
            ref: hue,
            class: "hue-slider",
            color: unref(color),
            vertical: "",
            disabled: unref(disabled)
          }, null, 8, ["color", "disabled"]),
          createVNode(SvPanel, {
            ref_key: "sv",
            ref: sv,
            color: unref(color),
            disabled: unref(disabled)
          }, null, 8, ["color", "disabled"])
        ], 2),
        _ctx.showAlpha ? (openBlock(), createBlock(AlphaSlider, {
          key: 0,
          ref_key: "alpha",
          ref: alpha,
          color: unref(color),
          disabled: unref(disabled)
        }, null, 8, ["color", "disabled"])) : createCommentVNode("v-if", true),
        _ctx.predefine ? (openBlock(), createBlock(Predefine, {
          key: 1,
          ref: "predefine",
          "enable-alpha": _ctx.showAlpha,
          color: unref(color),
          colors: _ctx.predefine,
          disabled: unref(disabled)
        }, null, 8, ["enable-alpha", "color", "colors", "disabled"])) : createCommentVNode("v-if", true),
        createElementVNode("div", {
          class: normalizeClass(unref(ns).e("footer"))
        }, [
          createVNode(unref(ElInput), {
            ref_key: "inputRef",
            ref: inputRef,
            modelValue: customInput.value,
            "onUpdate:modelValue": ($event) => customInput.value = $event,
            "validate-event": false,
            size: "small",
            disabled: unref(disabled),
            onChange: handleConfirm
          }, null, 8, ["modelValue", "onUpdate:modelValue", "disabled"]),
          renderSlot(_ctx.$slots, "footer")
        ], 2)
      ], 2);
    };
  }
});
var ColorPickerPanel = /* @__PURE__ */ _export_sfc(_sfc_main, [["__file", "color-picker-panel.vue"]]);

export { ColorPickerPanel as default };
//# sourceMappingURL=color-picker-panel2.mjs.map
