import { ref, computed } from 'vue';
import { isEqual } from 'lodash-unified';
import { useLocale } from '../../../../hooks/use-locale/index.mjs';
import { valueEquals, formatter, parseDate, dayOrDaysToDate } from '../utils.mjs';
import { isArray } from '@vue/shared';
import { UPDATE_MODEL_EVENT } from '../../../../constants/event.mjs';

const useCommonPicker = (props, emit) => {
  const { lang } = useLocale();
  const pickerVisible = ref(false);
  const pickerActualVisible = ref(false);
  const userInput = ref(null);
  const valueIsEmpty = computed(() => {
    const { modelValue } = props;
    return !modelValue || isArray(modelValue) && !modelValue.filter(Boolean).length;
  });
  const emitInput = (input) => {
    if (!valueEquals(props.modelValue, input)) {
      let formatted;
      if (isArray(input)) {
        formatted = input.map((item) => formatter(item, props.valueFormat, lang.value));
      } else if (input) {
        formatted = formatter(input, props.valueFormat, lang.value);
      }
      const emitVal = input ? formatted : input;
      emit(UPDATE_MODEL_EVENT, emitVal, lang.value);
    }
  };
  const parsedValue = computed(() => {
    var _a;
    let dayOrDays;
    if (valueIsEmpty.value) {
      if (pickerOptions.value.getDefaultValue) {
        dayOrDays = pickerOptions.value.getDefaultValue();
      }
    } else {
      if (isArray(props.modelValue)) {
        dayOrDays = props.modelValue.map((d) => parseDate(d, props.valueFormat, lang.value));
      } else {
        dayOrDays = parseDate((_a = props.modelValue) != null ? _a : "", props.valueFormat, lang.value);
      }
    }
    if (pickerOptions.value.getRangeAvailableTime) {
      const availableResult = pickerOptions.value.getRangeAvailableTime(dayOrDays);
      if (!isEqual(availableResult, dayOrDays)) {
        dayOrDays = availableResult;
        if (!valueIsEmpty.value) {
          emitInput(dayOrDaysToDate(dayOrDays));
        }
      }
    }
    if (isArray(dayOrDays) && dayOrDays.some((day) => !day)) {
      dayOrDays = [];
    }
    return dayOrDays;
  });
  const pickerOptions = ref({});
  const onSetPickerOption = (e) => {
    pickerOptions.value[e[0]] = e[1];
    pickerOptions.value.panelReady = true;
  };
  const onCalendarChange = (e) => {
    emit("calendar-change", e);
  };
  const onPanelChange = (value, mode, view) => {
    emit("panel-change", value, mode, view);
  };
  const onPick = (date = "", visible = false) => {
    pickerVisible.value = visible;
    let result;
    if (isArray(date)) {
      result = date.map((_) => _.toDate());
    } else {
      result = date ? date.toDate() : date;
    }
    userInput.value = null;
    emitInput(result);
  };
  return {
    parsedValue,
    pickerActualVisible,
    pickerOptions,
    pickerVisible,
    userInput,
    valueIsEmpty,
    emitInput,
    onCalendarChange,
    onPanelChange,
    onPick,
    onSetPickerOption
  };
};

export { useCommonPicker };
//# sourceMappingURL=use-common-picker.mjs.map
