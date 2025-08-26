import { defineComponent, inject, reactive, toRefs, provide, createVNode, mergeProps, isVNode } from 'vue';
import dayjs from 'dayjs';
import customParseFormat from 'dayjs/plugin/customParseFormat.js';
import advancedFormat from 'dayjs/plugin/advancedFormat.js';
import localeData from 'dayjs/plugin/localeData.js';
import weekOfYear from 'dayjs/plugin/weekOfYear.js';
import weekYear from 'dayjs/plugin/weekYear.js';
import dayOfYear from 'dayjs/plugin/dayOfYear.js';
import isSameOrAfter from 'dayjs/plugin/isSameOrAfter.js';
import isSameOrBefore from 'dayjs/plugin/isSameOrBefore.js';
import { datePickerPanelProps } from './props/date-picker-panel.mjs';
import { ROOT_PICKER_INJECTION_KEY } from './constants.mjs';
import { getPanel } from './panel-utils.mjs';
import { useCommonPicker } from '../../time-picker/src/composables/use-common-picker.mjs';
import { PICKER_BASE_INJECTION_KEY, ROOT_COMMON_PICKER_INJECTION_KEY } from '../../time-picker/src/constants.mjs';
import { UPDATE_MODEL_EVENT } from '../../../constants/event.mjs';
import { useNamespace } from '../../../hooks/use-namespace/index.mjs';
import { isUndefined } from '../../../utils/types.mjs';

function _isSlot(s) {
  return typeof s === "function" || Object.prototype.toString.call(s) === "[object Object]" && !isVNode(s);
}
dayjs.extend(localeData);
dayjs.extend(advancedFormat);
dayjs.extend(customParseFormat);
dayjs.extend(weekOfYear);
dayjs.extend(weekYear);
dayjs.extend(dayOfYear);
dayjs.extend(isSameOrAfter);
dayjs.extend(isSameOrBefore);
var DatePickerPanel = defineComponent({
  name: "ElDatePickerPanel",
  install: null,
  props: datePickerPanelProps,
  emits: [UPDATE_MODEL_EVENT, "calendar-change", "panel-change", "visible-change", "pick"],
  setup(props, {
    slots,
    emit
  }) {
    const ns = useNamespace("picker-panel");
    const pickerInjection = inject(PICKER_BASE_INJECTION_KEY, void 0);
    if (isUndefined(pickerInjection)) {
      const _props = reactive({
        ...toRefs(props)
      });
      provide(PICKER_BASE_INJECTION_KEY, {
        props: _props
      });
    }
    provide(ROOT_PICKER_INJECTION_KEY, {
      slots,
      pickerNs: ns
    });
    const {
      parsedValue,
      onCalendarChange,
      onPanelChange,
      onSetPickerOption,
      onPick
    } = inject(ROOT_COMMON_PICKER_INJECTION_KEY, () => useCommonPicker(props, emit), true);
    return () => {
      const Component = getPanel(props.type);
      return createVNode(Component, mergeProps(props, {
        "parsedValue": parsedValue.value,
        "onSet-picker-option": onSetPickerOption,
        "onCalendar-change": onCalendarChange,
        "onPanel-change": onPanelChange,
        "onPick": onPick
      }), _isSlot(slots) ? slots : {
        default: () => [slots]
      });
    };
  }
});

export { DatePickerPanel as default };
//# sourceMappingURL=date-picker-panel.mjs.map
