import { buildProps, definePropType } from '../../../../utils/vue/props/runtime.mjs';
import { datePickTypes } from '../../../../constants/date.mjs';
import { isArray } from '@vue/shared';

const selectionModes = [
  "date",
  "dates",
  "year",
  "years",
  "month",
  "months",
  "week",
  "range"
];
const datePickerSharedProps = buildProps({
  cellClassName: {
    type: definePropType(Function)
  },
  disabledDate: {
    type: definePropType(Function)
  },
  date: {
    type: definePropType(Object),
    required: true
  },
  minDate: {
    type: definePropType(Object)
  },
  maxDate: {
    type: definePropType(Object)
  },
  parsedValue: {
    type: definePropType([Object, Array])
  },
  rangeState: {
    type: definePropType(Object),
    default: () => ({
      endDate: null,
      selecting: false
    })
  },
  disabled: Boolean
});
const panelSharedProps = buildProps({
  type: {
    type: definePropType(String),
    required: true,
    values: datePickTypes
  },
  dateFormat: String,
  timeFormat: String,
  showNow: {
    type: Boolean,
    default: true
  },
  showConfirm: Boolean,
  showFooter: {
    type: Boolean,
    default: true
  },
  showWeekNumber: Boolean,
  border: Boolean,
  disabled: Boolean
});
const panelRangeSharedProps = buildProps({
  unlinkPanels: Boolean,
  visible: {
    type: Boolean,
    default: true
  },
  showConfirm: Boolean,
  showFooter: {
    type: Boolean,
    default: true
  },
  border: Boolean,
  disabled: Boolean,
  parsedValue: {
    type: definePropType(Array)
  }
});
const selectionModeWithDefault = (mode) => {
  return {
    type: String,
    values: selectionModes,
    default: mode
  };
};
const rangePickerSharedEmits = {
  pick: (range) => isArray(range)
};

export { datePickerSharedProps, panelRangeSharedProps, panelSharedProps, rangePickerSharedEmits, selectionModeWithDefault };
//# sourceMappingURL=shared.mjs.map
