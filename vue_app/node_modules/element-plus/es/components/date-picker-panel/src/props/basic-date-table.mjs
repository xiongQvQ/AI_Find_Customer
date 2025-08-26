import { datePickerSharedProps, selectionModeWithDefault } from './shared.mjs';
import { buildProps } from '../../../../utils/vue/props/runtime.mjs';

const basicDateTableProps = buildProps({
  ...datePickerSharedProps,
  showWeekNumber: Boolean,
  selectionMode: selectionModeWithDefault("date")
});
const basicDateTableEmits = ["changerange", "pick", "select"];

export { basicDateTableEmits, basicDateTableProps };
//# sourceMappingURL=basic-date-table.mjs.map
