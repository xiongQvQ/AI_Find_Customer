import { placements } from '@popperjs/core';
import { CircleClose, ArrowDown } from '@element-plus/icons-vue';
import { defaultProps } from '../../select-v2/src/useProps.mjs';
import { scrollbarEmits } from '../../scrollbar/src/scrollbar.mjs';
import { buildProps, definePropType } from '../../../utils/vue/props/runtime.mjs';
import { useSizeProp } from '../../../hooks/use-size/index.mjs';
import { useTooltipContentProps } from '../../tooltip/src/content.mjs';
import { iconPropType } from '../../../utils/vue/icon.mjs';
import { tagProps } from '../../tag/src/tag.mjs';
import { useEmptyValuesProps } from '../../../hooks/use-empty-values/index.mjs';
import { useAriaProps } from '../../../hooks/use-aria/index.mjs';
import { UPDATE_MODEL_EVENT, CHANGE_EVENT } from '../../../constants/event.mjs';

const selectProps = buildProps({
  name: String,
  id: String,
  modelValue: {
    type: definePropType([
      Array,
      String,
      Number,
      Boolean,
      Object
    ]),
    default: void 0
  },
  autocomplete: {
    type: String,
    default: "off"
  },
  automaticDropdown: Boolean,
  size: useSizeProp,
  effect: {
    type: definePropType(String),
    default: "light"
  },
  disabled: Boolean,
  clearable: Boolean,
  filterable: Boolean,
  allowCreate: Boolean,
  loading: Boolean,
  popperClass: {
    type: String,
    default: ""
  },
  popperStyle: {
    type: definePropType([String, Object])
  },
  popperOptions: {
    type: definePropType(Object),
    default: () => ({})
  },
  remote: Boolean,
  loadingText: String,
  noMatchText: String,
  noDataText: String,
  remoteMethod: {
    type: definePropType(Function)
  },
  filterMethod: {
    type: definePropType(Function)
  },
  multiple: Boolean,
  multipleLimit: {
    type: Number,
    default: 0
  },
  placeholder: {
    type: String
  },
  defaultFirstOption: Boolean,
  reserveKeyword: {
    type: Boolean,
    default: true
  },
  valueKey: {
    type: String,
    default: "value"
  },
  collapseTags: Boolean,
  collapseTagsTooltip: Boolean,
  maxCollapseTags: {
    type: Number,
    default: 1
  },
  teleported: useTooltipContentProps.teleported,
  persistent: {
    type: Boolean,
    default: true
  },
  clearIcon: {
    type: iconPropType,
    default: CircleClose
  },
  fitInputWidth: Boolean,
  suffixIcon: {
    type: iconPropType,
    default: ArrowDown
  },
  tagType: { ...tagProps.type, default: "info" },
  tagEffect: { ...tagProps.effect, default: "light" },
  validateEvent: {
    type: Boolean,
    default: true
  },
  remoteShowSuffix: Boolean,
  showArrow: {
    type: Boolean,
    default: true
  },
  offset: {
    type: Number,
    default: 12
  },
  placement: {
    type: definePropType(String),
    values: placements,
    default: "bottom-start"
  },
  fallbackPlacements: {
    type: definePropType(Array),
    default: ["bottom-start", "top-start", "right", "left"]
  },
  tabindex: {
    type: [String, Number],
    default: 0
  },
  appendTo: useTooltipContentProps.appendTo,
  options: {
    type: definePropType(Array)
  },
  props: {
    type: definePropType(Object),
    default: () => defaultProps
  },
  ...useEmptyValuesProps,
  ...useAriaProps(["ariaLabel"])
});
const selectEmits = {
  [UPDATE_MODEL_EVENT]: (val) => true,
  [CHANGE_EVENT]: (val) => true,
  "popup-scroll": scrollbarEmits.scroll,
  "remove-tag": (val) => true,
  "visible-change": (visible) => true,
  focus: (evt) => evt instanceof FocusEvent,
  blur: (evt) => evt instanceof FocusEvent,
  clear: () => true
};

export { selectEmits, selectProps };
//# sourceMappingURL=select.mjs.map
