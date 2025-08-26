import { popperContentProps } from '../../popper/src/content.mjs';
import { teleportProps } from '../../teleport/src/teleport.mjs';
import { buildProps, definePropType } from '../../../utils/vue/props/runtime.mjs';
import { useDelayedToggleProps } from '../../../hooks/use-delayed-toggle/index.mjs';
import { useAriaProps } from '../../../hooks/use-aria/index.mjs';

const useTooltipContentProps = buildProps({
  ...useDelayedToggleProps,
  ...popperContentProps,
  appendTo: {
    type: teleportProps.to.type
  },
  content: {
    type: String,
    default: ""
  },
  rawContent: Boolean,
  persistent: Boolean,
  visible: {
    type: definePropType(Boolean),
    default: null
  },
  transition: String,
  teleported: {
    type: Boolean,
    default: true
  },
  disabled: Boolean,
  ...useAriaProps(["ariaLabel"])
});

export { useTooltipContentProps };
//# sourceMappingURL=content.mjs.map
