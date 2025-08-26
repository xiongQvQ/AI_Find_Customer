import { computed } from 'vue';
import { buildProps, definePropType } from '../../../utils/vue/props/runtime.mjs';
import { NOOP } from '@vue/shared';
import { UPDATE_MODEL_EVENT, CHANGE_EVENT } from '../../../constants/event.mjs';

const CommonProps = buildProps({
  modelValue: {
    type: definePropType([Number, String, Array])
  },
  options: {
    type: definePropType(Array),
    default: () => []
  },
  props: {
    type: definePropType(Object),
    default: () => ({})
  }
});
const DefaultProps = {
  expandTrigger: "click",
  multiple: false,
  checkStrictly: false,
  emitPath: true,
  lazy: false,
  lazyLoad: NOOP,
  value: "value",
  label: "label",
  children: "children",
  leaf: "leaf",
  disabled: "disabled",
  hoverThreshold: 500,
  checkOnClickNode: false,
  checkOnClickLeaf: true,
  showPrefix: true
};
const cascaderPanelProps = buildProps({
  ...CommonProps,
  border: {
    type: Boolean,
    default: true
  },
  renderLabel: {
    type: Function
  }
});
const emitChangeFn = (value) => true;
const cascaderPanelEmits = {
  [UPDATE_MODEL_EVENT]: emitChangeFn,
  [CHANGE_EVENT]: emitChangeFn,
  close: () => true,
  "expand-change": (value) => value
};
const useCascaderConfig = (props) => {
  return computed(() => ({
    ...DefaultProps,
    ...props.props
  }));
};

export { CommonProps, DefaultProps, cascaderPanelEmits, cascaderPanelProps, useCascaderConfig };
//# sourceMappingURL=config.mjs.map
