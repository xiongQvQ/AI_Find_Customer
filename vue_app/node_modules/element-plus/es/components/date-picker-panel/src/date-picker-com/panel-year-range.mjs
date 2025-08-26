import { defineComponent, ref, inject, toRef, computed, useSlots, watch, openBlock, createElementBlock, normalizeClass, unref, createElementVNode, renderSlot, Fragment, renderList, toDisplayString, createCommentVNode, createVNode, withCtx } from 'vue';
import dayjs from 'dayjs';
import { DArrowLeft, DArrowRight } from '@element-plus/icons-vue';
import { ElIcon } from '../../../icon/index.mjs';
import { panelYearRangeProps, panelYearRangeEmits } from '../props/panel-year-range.mjs';
import { useYearRangeHeader } from '../composables/use-year-range-header.mjs';
import { useRangePicker } from '../composables/use-range-picker.mjs';
import { correctlyParseUserInput, isValidRange, getDefaultValue } from '../utils.mjs';
import { ROOT_PICKER_IS_DEFAULT_FORMAT_INJECTION_KEY } from '../constants.mjs';
import YearTable from './basic-year-table.mjs';
import _export_sfc from '../../../../_virtual/plugin-vue_export-helper.mjs';
import { useLocale } from '../../../../hooks/use-locale/index.mjs';
import { PICKER_BASE_INJECTION_KEY } from '../../../time-picker/src/constants.mjs';
import { isArray } from '@vue/shared';

const step = 10;
const unit = "year";
const __default__ = defineComponent({
  name: "DatePickerYearRange"
});
const _sfc_main = /* @__PURE__ */ defineComponent({
  ...__default__,
  props: panelYearRangeProps,
  emits: panelYearRangeEmits,
  setup(__props, { emit }) {
    const props = __props;
    const { lang } = useLocale();
    const leftDate = ref(dayjs().locale(lang.value));
    const rightDate = ref(dayjs().locale(lang.value).add(step, unit));
    const isDefaultFormat = inject(ROOT_PICKER_IS_DEFAULT_FORMAT_INJECTION_KEY, void 0);
    const pickerBase = inject(PICKER_BASE_INJECTION_KEY);
    const { shortcuts, disabledDate, cellClassName } = pickerBase.props;
    const format = toRef(pickerBase.props, "format");
    const defaultValue = toRef(pickerBase.props, "defaultValue");
    const {
      minDate,
      maxDate,
      rangeState,
      ppNs,
      drpNs,
      handleChangeRange,
      handleRangeConfirm,
      handleShortcutClick,
      onSelect,
      onReset
    } = useRangePicker(props, {
      defaultValue,
      leftDate,
      rightDate,
      step,
      unit,
      onParsedValueChanged
    });
    const {
      leftPrevYear,
      rightNextYear,
      leftNextYear,
      rightPrevYear,
      leftLabel,
      rightLabel,
      leftYear,
      rightYear
    } = useYearRangeHeader({
      unlinkPanels: toRef(props, "unlinkPanels"),
      leftDate,
      rightDate
    });
    const hasShortcuts = computed(() => !!shortcuts.length);
    const panelKls = computed(() => [
      ppNs.b(),
      drpNs.b(),
      ppNs.is("border", props.border),
      ppNs.is("disabled", props.disabled),
      {
        "has-sidebar": Boolean(useSlots().sidebar) || hasShortcuts.value
      }
    ]);
    const leftPanelKls = computed(() => {
      return {
        content: [ppNs.e("content"), drpNs.e("content"), "is-left"],
        arrowLeftBtn: [ppNs.e("icon-btn"), "d-arrow-left"],
        arrowRightBtn: [
          ppNs.e("icon-btn"),
          { [ppNs.is("disabled")]: !enableYearArrow.value },
          "d-arrow-right"
        ]
      };
    });
    const rightPanelKls = computed(() => {
      return {
        content: [ppNs.e("content"), drpNs.e("content"), "is-right"],
        arrowLeftBtn: [
          ppNs.e("icon-btn"),
          { "is-disabled": !enableYearArrow.value },
          "d-arrow-left"
        ],
        arrowRightBtn: [ppNs.e("icon-btn"), "d-arrow-right"]
      };
    });
    const enableYearArrow = computed(() => {
      return props.unlinkPanels && rightYear.value > leftYear.value + 1;
    });
    const handleRangePick = (val, close = true) => {
      const minDate_ = val.minDate;
      const maxDate_ = val.maxDate;
      if (maxDate.value === maxDate_ && minDate.value === minDate_) {
        return;
      }
      emit("calendar-change", [minDate_.toDate(), maxDate_ && maxDate_.toDate()]);
      maxDate.value = maxDate_;
      minDate.value = minDate_;
      if (!close)
        return;
      handleRangeConfirm();
    };
    const parseUserInput = (value) => {
      return correctlyParseUserInput(value, format.value, lang.value, isDefaultFormat);
    };
    const formatToString = (value) => {
      return isArray(value) ? value.map((day) => day.format(format.value)) : value.format(format.value);
    };
    const isValidValue = (date) => {
      return isValidRange(date) && (disabledDate ? !disabledDate(date[0].toDate()) && !disabledDate(date[1].toDate()) : true);
    };
    const handleClear = () => {
      const defaultArr = getDefaultValue(unref(defaultValue), {
        lang: unref(lang),
        step,
        unit,
        unlinkPanels: props.unlinkPanels
      });
      leftDate.value = defaultArr[0];
      rightDate.value = defaultArr[1];
      emit("pick", null);
    };
    function onParsedValueChanged(minDate2, maxDate2) {
      if (props.unlinkPanels && maxDate2) {
        const minDateYear = (minDate2 == null ? void 0 : minDate2.year()) || 0;
        const maxDateYear = maxDate2.year();
        rightDate.value = minDateYear + step > maxDateYear ? maxDate2.add(step, unit) : maxDate2;
      } else {
        rightDate.value = leftDate.value.add(step, unit);
      }
    }
    watch(() => props.visible, (visible) => {
      if (!visible && rangeState.value.selecting) {
        onReset(props.parsedValue);
        onSelect(false);
      }
    });
    emit("set-picker-option", ["isValidValue", isValidValue]);
    emit("set-picker-option", ["parseUserInput", parseUserInput]);
    emit("set-picker-option", ["formatToString", formatToString]);
    emit("set-picker-option", ["handleClear", handleClear]);
    return (_ctx, _cache) => {
      return openBlock(), createElementBlock("div", {
        class: normalizeClass(unref(panelKls))
      }, [
        createElementVNode("div", {
          class: normalizeClass(unref(ppNs).e("body-wrapper"))
        }, [
          renderSlot(_ctx.$slots, "sidebar", {
            class: normalizeClass(unref(ppNs).e("sidebar"))
          }),
          unref(hasShortcuts) ? (openBlock(), createElementBlock("div", {
            key: 0,
            class: normalizeClass(unref(ppNs).e("sidebar"))
          }, [
            (openBlock(true), createElementBlock(Fragment, null, renderList(unref(shortcuts), (shortcut, key) => {
              return openBlock(), createElementBlock("button", {
                key,
                type: "button",
                class: normalizeClass(unref(ppNs).e("shortcut")),
                disabled: _ctx.disabled,
                onClick: ($event) => unref(handleShortcutClick)(shortcut)
              }, toDisplayString(shortcut.text), 11, ["disabled", "onClick"]);
            }), 128))
          ], 2)) : createCommentVNode("v-if", true),
          createElementVNode("div", {
            class: normalizeClass(unref(ppNs).e("body"))
          }, [
            createElementVNode("div", {
              class: normalizeClass(unref(leftPanelKls).content)
            }, [
              createElementVNode("div", {
                class: normalizeClass(unref(drpNs).e("header"))
              }, [
                createElementVNode("button", {
                  type: "button",
                  class: normalizeClass(unref(leftPanelKls).arrowLeftBtn),
                  disabled: _ctx.disabled,
                  onClick: unref(leftPrevYear)
                }, [
                  renderSlot(_ctx.$slots, "prev-year", {}, () => [
                    createVNode(unref(ElIcon), null, {
                      default: withCtx(() => [
                        createVNode(unref(DArrowLeft))
                      ]),
                      _: 1
                    })
                  ])
                ], 10, ["disabled", "onClick"]),
                _ctx.unlinkPanels ? (openBlock(), createElementBlock("button", {
                  key: 0,
                  type: "button",
                  disabled: !unref(enableYearArrow) || _ctx.disabled,
                  class: normalizeClass(unref(leftPanelKls).arrowRightBtn),
                  onClick: unref(leftNextYear)
                }, [
                  renderSlot(_ctx.$slots, "next-year", {}, () => [
                    createVNode(unref(ElIcon), null, {
                      default: withCtx(() => [
                        createVNode(unref(DArrowRight))
                      ]),
                      _: 1
                    })
                  ])
                ], 10, ["disabled", "onClick"])) : createCommentVNode("v-if", true),
                createElementVNode("div", null, toDisplayString(unref(leftLabel)), 1)
              ], 2),
              createVNode(YearTable, {
                "selection-mode": "range",
                date: leftDate.value,
                "min-date": unref(minDate),
                "max-date": unref(maxDate),
                "range-state": unref(rangeState),
                "disabled-date": unref(disabledDate),
                disabled: _ctx.disabled,
                "cell-class-name": unref(cellClassName),
                onChangerange: unref(handleChangeRange),
                onPick: handleRangePick,
                onSelect: unref(onSelect)
              }, null, 8, ["date", "min-date", "max-date", "range-state", "disabled-date", "disabled", "cell-class-name", "onChangerange", "onSelect"])
            ], 2),
            createElementVNode("div", {
              class: normalizeClass(unref(rightPanelKls).content)
            }, [
              createElementVNode("div", {
                class: normalizeClass(unref(drpNs).e("header"))
              }, [
                _ctx.unlinkPanels ? (openBlock(), createElementBlock("button", {
                  key: 0,
                  type: "button",
                  disabled: !unref(enableYearArrow) || _ctx.disabled,
                  class: normalizeClass(unref(rightPanelKls).arrowLeftBtn),
                  onClick: unref(rightPrevYear)
                }, [
                  renderSlot(_ctx.$slots, "prev-year", {}, () => [
                    createVNode(unref(ElIcon), null, {
                      default: withCtx(() => [
                        createVNode(unref(DArrowLeft))
                      ]),
                      _: 1
                    })
                  ])
                ], 10, ["disabled", "onClick"])) : createCommentVNode("v-if", true),
                createElementVNode("button", {
                  type: "button",
                  class: normalizeClass(unref(rightPanelKls).arrowRightBtn),
                  disabled: _ctx.disabled,
                  onClick: unref(rightNextYear)
                }, [
                  renderSlot(_ctx.$slots, "next-year", {}, () => [
                    createVNode(unref(ElIcon), null, {
                      default: withCtx(() => [
                        createVNode(unref(DArrowRight))
                      ]),
                      _: 1
                    })
                  ])
                ], 10, ["disabled", "onClick"]),
                createElementVNode("div", null, toDisplayString(unref(rightLabel)), 1)
              ], 2),
              createVNode(YearTable, {
                "selection-mode": "range",
                date: rightDate.value,
                "min-date": unref(minDate),
                "max-date": unref(maxDate),
                "range-state": unref(rangeState),
                "disabled-date": unref(disabledDate),
                disabled: _ctx.disabled,
                "cell-class-name": unref(cellClassName),
                onChangerange: unref(handleChangeRange),
                onPick: handleRangePick,
                onSelect: unref(onSelect)
              }, null, 8, ["date", "min-date", "max-date", "range-state", "disabled-date", "disabled", "cell-class-name", "onChangerange", "onSelect"])
            ], 2)
          ], 2)
        ], 2)
      ], 2);
    };
  }
});
var YearRangePickPanel = /* @__PURE__ */ _export_sfc(_sfc_main, [["__file", "panel-year-range.vue"]]);

export { YearRangePickPanel as default };
//# sourceMappingURL=panel-year-range.mjs.map
