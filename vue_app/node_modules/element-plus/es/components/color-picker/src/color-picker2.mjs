import { defineComponent, ref, computed, watch, provide, openBlock, createBlock, unref, withCtx, withDirectives, mergeProps, withKeys, createElementVNode, createVNode, normalizeClass, createTextVNode, toDisplayString, normalizeStyle, vShow, nextTick } from 'vue';
import { pick, debounce } from 'lodash-unified';
import { ElIcon } from '../../icon/index.mjs';
import { reactiveComputed } from '@vueuse/core';
import { ElTooltip } from '../../tooltip/index.mjs';
import { ElButton } from '../../button/index.mjs';
import { ArrowDown, Close } from '@element-plus/icons-vue';
import { colorPickerProps, colorPickerEmits } from './color-picker.mjs';
import { ElColorPickerPanel } from '../../color-picker-panel/index.mjs';
import Color from '../../color-picker-panel/src/utils/color.mjs';
import { useCommonColor } from '../../color-picker-panel/src/composables/use-common-color.mjs';
import _export_sfc from '../../../_virtual/plugin-vue_export-helper.mjs';
import { colorPickerPanelProps, ROOT_COMMON_COLOR_INJECTION_KEY } from '../../color-picker-panel/src/color-picker-panel.mjs';
import ClickOutside from '../../../directives/click-outside/index.mjs';
import { useLocale } from '../../../hooks/use-locale/index.mjs';
import { useNamespace } from '../../../hooks/use-namespace/index.mjs';
import { useFormItem, useFormItemInputId } from '../../form/src/hooks/use-form-item.mjs';
import { useFormSize, useFormDisabled } from '../../form/src/hooks/use-form-common-props.mjs';
import { useEmptyValues } from '../../../hooks/use-empty-values/index.mjs';
import { useFocusController } from '../../../hooks/use-focus-controller/index.mjs';
import { UPDATE_MODEL_EVENT, CHANGE_EVENT } from '../../../constants/event.mjs';
import { debugWarn } from '../../../utils/error.mjs';
import { EVENT_CODE } from '../../../constants/aria.mjs';

const __default__ = defineComponent({
  name: "ElColorPicker"
});
const _sfc_main = /* @__PURE__ */ defineComponent({
  ...__default__,
  props: colorPickerProps,
  emits: colorPickerEmits,
  setup(__props, { expose, emit }) {
    const props = __props;
    const { t } = useLocale();
    const ns = useNamespace("color");
    const { formItem } = useFormItem();
    const colorSize = useFormSize();
    const colorDisabled = useFormDisabled();
    const { valueOnClear, isEmptyValue } = useEmptyValues(props, null);
    const commonColor = useCommonColor(props, emit);
    const { inputId: buttonId, isLabeledByFormItem } = useFormItemInputId(props, {
      formItemContext: formItem
    });
    const popper = ref();
    const triggerRef = ref();
    const pickerPanelRef = ref();
    const showPicker = ref(false);
    const showPanelColor = ref(false);
    let shouldActiveChange = true;
    const { isFocused, handleFocus, handleBlur } = useFocusController(triggerRef, {
      disabled: colorDisabled,
      beforeBlur(event) {
        var _a;
        return (_a = popper.value) == null ? void 0 : _a.isFocusInsideContent(event);
      },
      afterBlur() {
        setShowPicker(false);
        resetColor();
      }
    });
    const color = reactiveComputed(() => {
      var _a, _b;
      return (_b = (_a = pickerPanelRef.value) == null ? void 0 : _a.color) != null ? _b : commonColor.color;
    });
    const panelProps = computed(() => pick(props, Object.keys(colorPickerPanelProps)));
    const displayedColor = computed(() => {
      if (!props.modelValue && !showPanelColor.value) {
        return "transparent";
      }
      return displayedRgb(color, props.showAlpha);
    });
    const currentColor = computed(() => {
      return !props.modelValue && !showPanelColor.value ? "" : color.value;
    });
    const buttonAriaLabel = computed(() => {
      return !isLabeledByFormItem.value ? props.ariaLabel || t("el.colorpicker.defaultLabel") : void 0;
    });
    const buttonAriaLabelledby = computed(() => {
      return isLabeledByFormItem.value ? formItem == null ? void 0 : formItem.labelId : void 0;
    });
    const btnKls = computed(() => {
      return [
        ns.b("picker"),
        ns.is("disabled", colorDisabled.value),
        ns.bm("picker", colorSize.value),
        ns.is("focused", isFocused.value)
      ];
    });
    function displayedRgb(color2, showAlpha) {
      const { r, g, b, a } = color2.toRgb();
      return showAlpha ? `rgba(${r}, ${g}, ${b}, ${a})` : `rgb(${r}, ${g}, ${b})`;
    }
    function setShowPicker(value) {
      showPicker.value = value;
    }
    const debounceSetShowPicker = debounce(setShowPicker, 100, { leading: true });
    function show() {
      if (colorDisabled.value)
        return;
      setShowPicker(true);
    }
    function hide() {
      debounceSetShowPicker(false);
      resetColor();
    }
    function resetColor() {
      nextTick(() => {
        if (props.modelValue) {
          color.fromString(props.modelValue);
        } else {
          color.value = "";
          nextTick(() => {
            showPanelColor.value = false;
          });
        }
      });
    }
    function handleTrigger() {
      if (colorDisabled.value)
        return;
      if (showPicker.value) {
        resetColor();
      }
      debounceSetShowPicker(!showPicker.value);
    }
    function confirmValue() {
      const value = isEmptyValue(color.value) ? valueOnClear.value : color.value;
      emit(UPDATE_MODEL_EVENT, value);
      emit(CHANGE_EVENT, value);
      if (props.validateEvent) {
        formItem == null ? void 0 : formItem.validate("change").catch((err) => debugWarn());
      }
      debounceSetShowPicker(false);
      nextTick(() => {
        const newColor = new Color({
          enableAlpha: props.showAlpha,
          format: props.colorFormat || "",
          value: props.modelValue
        });
        if (!color.compare(newColor)) {
          resetColor();
        }
      });
    }
    function clear() {
      debounceSetShowPicker(false);
      emit(UPDATE_MODEL_EVENT, valueOnClear.value);
      emit(CHANGE_EVENT, valueOnClear.value);
      if (props.modelValue !== valueOnClear.value && props.validateEvent) {
        formItem == null ? void 0 : formItem.validate("change").catch((err) => debugWarn());
      }
      resetColor();
    }
    function handleClickOutside() {
      if (!showPicker.value)
        return;
      hide();
      isFocused.value && focus();
    }
    function handleEsc(event) {
      event.preventDefault();
      event.stopPropagation();
      setShowPicker(false);
      resetColor();
    }
    function handleKeyDown(event) {
      var _a, _b;
      switch (event.code) {
        case EVENT_CODE.enter:
        case EVENT_CODE.numpadEnter:
        case EVENT_CODE.space:
          event.preventDefault();
          event.stopPropagation();
          show();
          (_b = (_a = pickerPanelRef == null ? void 0 : pickerPanelRef.value) == null ? void 0 : _a.inputRef) == null ? void 0 : _b.focus();
          break;
        case EVENT_CODE.esc:
          handleEsc(event);
          break;
      }
    }
    function focus() {
      triggerRef.value.focus();
    }
    function blur() {
      triggerRef.value.blur();
    }
    watch(() => currentColor.value, (val) => {
      shouldActiveChange && emit("activeChange", val);
      shouldActiveChange = true;
    });
    watch(() => color.value, () => {
      if (!props.modelValue && !showPanelColor.value) {
        showPanelColor.value = true;
      }
    });
    watch(() => props.modelValue, (newVal) => {
      if (!newVal) {
        showPanelColor.value = false;
      } else if (newVal && newVal !== color.value) {
        shouldActiveChange = false;
        color.fromString(newVal);
      }
    });
    provide(ROOT_COMMON_COLOR_INJECTION_KEY, commonColor);
    expose({
      color,
      show,
      hide,
      focus,
      blur
    });
    return (_ctx, _cache) => {
      return openBlock(), createBlock(unref(ElTooltip), {
        ref_key: "popper",
        ref: popper,
        visible: showPicker.value,
        "show-arrow": false,
        "fallback-placements": ["bottom", "top", "right", "left"],
        offset: 0,
        "gpu-acceleration": false,
        "popper-class": [unref(ns).be("picker", "panel"), _ctx.popperClass],
        "stop-popper-mouse-event": false,
        pure: "",
        effect: "light",
        trigger: "click",
        teleported: _ctx.teleported,
        transition: `${unref(ns).namespace.value}-zoom-in-top`,
        persistent: _ctx.persistent,
        "append-to": _ctx.appendTo,
        onHide: ($event) => setShowPicker(false)
      }, {
        content: withCtx(() => [
          withDirectives((openBlock(), createBlock(unref(ElColorPickerPanel), mergeProps({
            ref_key: "pickerPanelRef",
            ref: pickerPanelRef
          }, unref(panelProps), {
            border: false,
            onKeydown: withKeys(handleEsc, ["esc"])
          }), {
            footer: withCtx(() => [
              createElementVNode("div", null, [
                createVNode(unref(ElButton), {
                  class: normalizeClass(unref(ns).be("footer", "link-btn")),
                  text: "",
                  size: "small",
                  onClick: clear
                }, {
                  default: withCtx(() => [
                    createTextVNode(toDisplayString(unref(t)("el.colorpicker.clear")), 1)
                  ]),
                  _: 1
                }, 8, ["class"]),
                createVNode(unref(ElButton), {
                  plain: "",
                  size: "small",
                  class: normalizeClass(unref(ns).be("footer", "btn")),
                  onClick: confirmValue
                }, {
                  default: withCtx(() => [
                    createTextVNode(toDisplayString(unref(t)("el.colorpicker.confirm")), 1)
                  ]),
                  _: 1
                }, 8, ["class"])
              ])
            ]),
            _: 1
          }, 16, ["onKeydown"])), [
            [unref(ClickOutside), handleClickOutside, triggerRef.value]
          ])
        ]),
        default: withCtx(() => [
          createElementVNode("div", mergeProps({
            id: unref(buttonId),
            ref_key: "triggerRef",
            ref: triggerRef
          }, _ctx.$attrs, {
            class: unref(btnKls),
            role: "button",
            "aria-label": unref(buttonAriaLabel),
            "aria-labelledby": unref(buttonAriaLabelledby),
            "aria-description": unref(t)("el.colorpicker.description", { color: _ctx.modelValue || "" }),
            "aria-disabled": unref(colorDisabled),
            tabindex: unref(colorDisabled) ? void 0 : _ctx.tabindex,
            onKeydown: handleKeyDown,
            onFocus: unref(handleFocus),
            onBlur: unref(handleBlur)
          }), [
            createElementVNode("div", {
              class: normalizeClass(unref(ns).be("picker", "trigger")),
              onClick: handleTrigger
            }, [
              createElementVNode("span", {
                class: normalizeClass([unref(ns).be("picker", "color"), unref(ns).is("alpha", _ctx.showAlpha)])
              }, [
                createElementVNode("span", {
                  class: normalizeClass(unref(ns).be("picker", "color-inner")),
                  style: normalizeStyle({
                    backgroundColor: unref(displayedColor)
                  })
                }, [
                  withDirectives(createVNode(unref(ElIcon), {
                    class: normalizeClass([unref(ns).be("picker", "icon"), unref(ns).is("icon-arrow-down")])
                  }, {
                    default: withCtx(() => [
                      createVNode(unref(ArrowDown))
                    ]),
                    _: 1
                  }, 8, ["class"]), [
                    [vShow, _ctx.modelValue || showPanelColor.value]
                  ]),
                  withDirectives(createVNode(unref(ElIcon), {
                    class: normalizeClass([unref(ns).be("picker", "empty"), unref(ns).is("icon-close")])
                  }, {
                    default: withCtx(() => [
                      createVNode(unref(Close))
                    ]),
                    _: 1
                  }, 8, ["class"]), [
                    [vShow, !_ctx.modelValue && !showPanelColor.value]
                  ])
                ], 6)
              ], 2)
            ], 2)
          ], 16, ["id", "aria-label", "aria-labelledby", "aria-description", "aria-disabled", "tabindex", "onFocus", "onBlur"])
        ]),
        _: 1
      }, 8, ["visible", "popper-class", "teleported", "transition", "persistent", "append-to", "onHide"]);
    };
  }
});
var ColorPicker = /* @__PURE__ */ _export_sfc(_sfc_main, [["__file", "color-picker.vue"]]);

export { ColorPicker as default };
//# sourceMappingURL=color-picker2.mjs.map
