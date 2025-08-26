import DatePickerPanel from './src/date-picker-panel.mjs';
export { ROOT_PICKER_INJECTION_KEY, ROOT_PICKER_IS_DEFAULT_FORMAT_INJECTION_KEY } from './src/constants.mjs';
export { datePickerPanelProps } from './src/props/date-picker-panel.mjs';
import { withInstall } from '../../utils/vue/install.mjs';

const ElDatePickerPanel = withInstall(DatePickerPanel);

export { ElDatePickerPanel, ElDatePickerPanel as default };
//# sourceMappingURL=index.mjs.map
