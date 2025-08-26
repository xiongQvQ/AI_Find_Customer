import { tagProps } from '../../tag/src/tag.mjs';
import { CircleClose } from '@element-plus/icons-vue';
import { buildProps, definePropType } from '../../../utils/vue/props/runtime.mjs';
import { EVENT_CODE } from '../../../constants/aria.mjs';
import { useSizeProp } from '../../../hooks/use-size/index.mjs';
import { iconPropType } from '../../../utils/vue/icon.mjs';
import { UPDATE_MODEL_EVENT, CHANGE_EVENT, INPUT_EVENT } from '../../../constants/event.mjs';
import { isArray, isString } from '@vue/shared';
import { isUndefined } from '../../../utils/types.mjs';

const inputTagProps = buildProps({
  modelValue: {
    type: definePropType(Array)
  },
  max: Number,
  tagType: { ...tagProps.type, default: "info" },
  tagEffect: tagProps.effect,
  trigger: {
    type: definePropType(String),
    default: EVENT_CODE.enter
  },
  draggable: Boolean,
  delimiter: {
    type: [String, RegExp],
    default: ""
  },
  size: useSizeProp,
  clearable: Boolean,
  clearIcon: {
    type: iconPropType,
    default: CircleClose
  },
  disabled: {
    type: Boolean,
    default: void 0
  },
  validateEvent: {
    type: Boolean,
    default: true
  },
  readonly: Boolean,
  autofocus: Boolean,
  id: {
    type: String,
    default: void 0
  },
  tabindex: {
    type: [String, Number],
    default: 0
  },
  maxlength: {
    type: [String, Number]
  },
  minlength: {
    type: [String, Number]
  },
  placeholder: String,
  autocomplete: {
    type: String,
    default: "off"
  },
  saveOnBlur: {
    type: Boolean,
    default: true
  },
  collapseTags: Boolean,
  collapseTagsTooltip: Boolean,
  maxCollapseTags: {
    type: Number,
    default: 1
  },
  ariaLabel: String
});
const inputTagEmits = {
  [UPDATE_MODEL_EVENT]: (value) => isArray(value) || isUndefined(value),
  [CHANGE_EVENT]: (value) => isArray(value) || isUndefined(value),
  [INPUT_EVENT]: (value) => isString(value),
  "add-tag": (value) => isString(value) || isArray(value),
  "remove-tag": (value) => isString(value),
  focus: (evt) => evt instanceof FocusEvent,
  blur: (evt) => evt instanceof FocusEvent,
  clear: () => true
};

export { inputTagEmits, inputTagProps };
//# sourceMappingURL=input-tag.mjs.map
