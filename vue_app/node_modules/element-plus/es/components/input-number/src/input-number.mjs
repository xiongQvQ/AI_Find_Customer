import { isNil } from 'lodash-unified';
import { buildProps, definePropType } from '../../../utils/vue/props/runtime.mjs';
import { useSizeProp } from '../../../hooks/use-size/index.mjs';
import { isNumber } from '../../../utils/types.mjs';
import { useAriaProps } from '../../../hooks/use-aria/index.mjs';
import { CHANGE_EVENT, INPUT_EVENT, UPDATE_MODEL_EVENT } from '../../../constants/event.mjs';

const inputNumberProps = buildProps({
  id: {
    type: String,
    default: void 0
  },
  step: {
    type: Number,
    default: 1
  },
  stepStrictly: Boolean,
  max: {
    type: Number,
    default: Number.MAX_SAFE_INTEGER
  },
  min: {
    type: Number,
    default: Number.MIN_SAFE_INTEGER
  },
  modelValue: {
    type: [Number, null]
  },
  readonly: Boolean,
  disabled: Boolean,
  size: useSizeProp,
  controls: {
    type: Boolean,
    default: true
  },
  controlsPosition: {
    type: String,
    default: "",
    values: ["", "right"]
  },
  valueOnClear: {
    type: [String, Number, null],
    validator: (val) => val === null || isNumber(val) || ["min", "max"].includes(val),
    default: null
  },
  name: String,
  placeholder: String,
  precision: {
    type: Number,
    validator: (val) => val >= 0 && val === Number.parseInt(`${val}`, 10)
  },
  validateEvent: {
    type: Boolean,
    default: true
  },
  ...useAriaProps(["ariaLabel"]),
  inputmode: {
    type: definePropType(String),
    default: void 0
  },
  align: {
    type: definePropType(String),
    default: "center"
  },
  disabledScientific: Boolean
});
const inputNumberEmits = {
  [CHANGE_EVENT]: (cur, prev) => prev !== cur,
  blur: (e) => e instanceof FocusEvent,
  focus: (e) => e instanceof FocusEvent,
  [INPUT_EVENT]: (val) => isNumber(val) || isNil(val),
  [UPDATE_MODEL_EVENT]: (val) => isNumber(val) || isNil(val)
};

export { inputNumberEmits, inputNumberProps };
//# sourceMappingURL=input-number.mjs.map
