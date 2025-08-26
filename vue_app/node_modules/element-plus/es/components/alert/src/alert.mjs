import { useDelayedToggleProps } from '../../../hooks/use-delayed-toggle/index.mjs';
import { TypeComponentsMap } from '../../../utils/vue/icon.mjs';
import { buildProps } from '../../../utils/vue/props/runtime.mjs';
import { keysOf } from '../../../utils/objects.mjs';
import { isUndefined } from '../../../utils/types.mjs';

const alertEffects = ["light", "dark"];
const alertProps = buildProps({
  title: {
    type: String,
    default: ""
  },
  description: {
    type: String,
    default: ""
  },
  type: {
    type: String,
    values: keysOf(TypeComponentsMap),
    default: "info"
  },
  closable: {
    type: Boolean,
    default: true
  },
  closeText: {
    type: String,
    default: ""
  },
  showIcon: Boolean,
  center: Boolean,
  effect: {
    type: String,
    values: alertEffects,
    default: "light"
  },
  ...useDelayedToggleProps
});
const alertEmits = {
  open: () => true,
  close: (evt) => isUndefined(evt) || evt instanceof Event
};

export { alertEffects, alertEmits, alertProps };
//# sourceMappingURL=alert.mjs.map
