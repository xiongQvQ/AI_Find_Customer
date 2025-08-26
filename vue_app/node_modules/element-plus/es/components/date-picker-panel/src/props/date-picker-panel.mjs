import { disabledTimeListsProps } from '../../../time-picker/src/props/shared.mjs';
import { buildProps, definePropType } from '../../../../utils/vue/props/runtime.mjs';

const datePickerPanelProps = buildProps({
  valueFormat: String,
  dateFormat: String,
  timeFormat: String,
  disabled: Boolean,
  modelValue: {
    type: definePropType([Date, Array, String, Number]),
    default: ""
  },
  defaultValue: {
    type: definePropType([Date, Array])
  },
  defaultTime: {
    type: definePropType([Date, Array])
  },
  isRange: Boolean,
  ...disabledTimeListsProps,
  disabledDate: {
    type: Function
  },
  cellClassName: {
    type: Function
  },
  shortcuts: {
    type: Array,
    default: () => []
  },
  arrowControl: Boolean,
  unlinkPanels: Boolean,
  showNow: {
    type: Boolean,
    default: true
  },
  showConfirm: Boolean,
  showFooter: Boolean,
  showWeekNumber: Boolean,
  type: {
    type: definePropType(String),
    default: "date"
  },
  clearable: {
    type: Boolean,
    default: true
  },
  border: {
    type: Boolean,
    default: true
  }
});

export { datePickerPanelProps };
//# sourceMappingURL=date-picker-panel.mjs.map
