import { defineComponent, computed, provide, reactive, toRef, ref, createVNode, mergeProps, isVNode } from 'vue';
import '../../time-picker/index.mjs';
import { ElDatePickerPanel } from '../../date-picker-panel/index.mjs';
import { datePickerProps } from './props.mjs';
import { ROOT_PICKER_IS_DEFAULT_FORMAT_INJECTION_KEY } from '../../date-picker-panel/src/constants.mjs';
import { PICKER_POPPER_OPTIONS_INJECTION_KEY, DEFAULT_FORMATS_DATEPICKER, DEFAULT_FORMATS_DATE } from '../../time-picker/src/constants.mjs';
import CommonPicker from '../../time-picker/src/common/picker.mjs';
import { UPDATE_MODEL_EVENT } from '../../../constants/event.mjs';

function _isSlot(s) {
  return typeof s === "function" || Object.prototype.toString.call(s) === "[object Object]" && !isVNode(s);
}
var DatePicker = defineComponent({
  name: "ElDatePicker",
  install: null,
  props: datePickerProps,
  emits: [UPDATE_MODEL_EVENT],
  setup(props, {
    expose,
    emit,
    slots
  }) {
    const isDefaultFormat = computed(() => {
      return !props.format;
    });
    provide(ROOT_PICKER_IS_DEFAULT_FORMAT_INJECTION_KEY, isDefaultFormat);
    provide(PICKER_POPPER_OPTIONS_INJECTION_KEY, reactive(toRef(props, "popperOptions")));
    const commonPicker = ref();
    const refProps = {
      focus: () => {
        var _a;
        (_a = commonPicker.value) == null ? void 0 : _a.focus();
      },
      blur: () => {
        var _a;
        (_a = commonPicker.value) == null ? void 0 : _a.blur();
      },
      handleOpen: () => {
        var _a;
        (_a = commonPicker.value) == null ? void 0 : _a.handleOpen();
      },
      handleClose: () => {
        var _a;
        (_a = commonPicker.value) == null ? void 0 : _a.handleClose();
      }
    };
    expose(refProps);
    const onModelValueUpdated = (val) => {
      emit(UPDATE_MODEL_EVENT, val);
    };
    return () => {
      var _a;
      const format = (_a = props.format) != null ? _a : DEFAULT_FORMATS_DATEPICKER[props.type] || DEFAULT_FORMATS_DATE;
      return createVNode(CommonPicker, mergeProps(props, {
        "format": format,
        "type": props.type,
        "ref": commonPicker,
        "onUpdate:modelValue": onModelValueUpdated
      }), {
        default: (scopedProps) => createVNode(ElDatePickerPanel, mergeProps({
          "border": false
        }, scopedProps), _isSlot(slots) ? slots : {
          default: () => [slots]
        }),
        "range-separator": slots["range-separator"]
      });
    };
  }
});

export { DatePicker as default };
//# sourceMappingURL=date-picker.mjs.map
