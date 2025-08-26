import { buildProps } from '../../../utils/vue/props/runtime.mjs';
import { iconPropType } from '../../../utils/vue/icon.mjs';

const linkProps = buildProps({
  type: {
    type: String,
    values: ["primary", "success", "warning", "info", "danger", "default"],
    default: void 0
  },
  underline: {
    type: [Boolean, String],
    values: [true, false, "always", "never", "hover"],
    default: void 0
  },
  disabled: Boolean,
  href: { type: String, default: "" },
  target: {
    type: String,
    default: "_self"
  },
  icon: {
    type: iconPropType
  }
});
const linkEmits = {
  click: (evt) => evt instanceof MouseEvent
};

export { linkEmits, linkProps };
//# sourceMappingURL=link.mjs.map
