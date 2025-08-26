import { inputProps } from '../../input/src/input2.mjs';
import { useTooltipContentProps } from '../../tooltip/src/content.mjs';
import { buildProps, definePropType } from '../../../utils/vue/props/runtime.mjs';
import { NOOP, isString, isObject } from '@vue/shared';
import { UPDATE_MODEL_EVENT, INPUT_EVENT, CHANGE_EVENT } from '../../../constants/event.mjs';

const autocompleteProps = buildProps({
  ...inputProps,
  valueKey: {
    type: String,
    default: "value"
  },
  modelValue: {
    type: [String, Number],
    default: ""
  },
  debounce: {
    type: Number,
    default: 300
  },
  placement: {
    type: definePropType(String),
    values: [
      "top",
      "top-start",
      "top-end",
      "bottom",
      "bottom-start",
      "bottom-end"
    ],
    default: "bottom-start"
  },
  fetchSuggestions: {
    type: definePropType([Function, Array]),
    default: NOOP
  },
  popperClass: {
    type: String,
    default: ""
  },
  triggerOnFocus: {
    type: Boolean,
    default: true
  },
  selectWhenUnmatched: Boolean,
  hideLoading: Boolean,
  teleported: useTooltipContentProps.teleported,
  appendTo: useTooltipContentProps.appendTo,
  highlightFirstItem: Boolean,
  fitInputWidth: Boolean
});
const autocompleteEmits = {
  [UPDATE_MODEL_EVENT]: (value) => isString(value),
  [INPUT_EVENT]: (value) => isString(value),
  [CHANGE_EVENT]: (value) => isString(value),
  focus: (evt) => evt instanceof FocusEvent,
  blur: (evt) => evt instanceof FocusEvent,
  clear: () => true,
  select: (item) => isObject(item)
};

export { autocompleteEmits, autocompleteProps };
//# sourceMappingURL=autocomplete.mjs.map
