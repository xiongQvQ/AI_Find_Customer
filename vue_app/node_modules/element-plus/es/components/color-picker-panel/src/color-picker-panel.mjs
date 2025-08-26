import { isNil } from 'lodash-unified';
import { buildProps, definePropType } from '../../../utils/vue/props/runtime.mjs';
import { UPDATE_MODEL_EVENT } from '../../../constants/event.mjs';
import { isString } from '@vue/shared';

const colorPickerPanelProps = buildProps({
  modelValue: {
    type: definePropType(String),
    default: void 0
  },
  border: {
    type: Boolean,
    default: true
  },
  showAlpha: Boolean,
  colorFormat: String,
  disabled: Boolean,
  predefine: {
    type: definePropType(Array)
  }
});
const colorPickerPanelEmits = {
  [UPDATE_MODEL_EVENT]: (val) => isString(val) || isNil(val)
};
const ROOT_COMMON_COLOR_INJECTION_KEY = Symbol("colorCommonPickerKey");
const colorPickerPanelContextKey = Symbol("colorPickerPanelContextKey");

export { ROOT_COMMON_COLOR_INJECTION_KEY, colorPickerPanelContextKey, colorPickerPanelEmits, colorPickerPanelProps };
//# sourceMappingURL=color-picker-panel.mjs.map
