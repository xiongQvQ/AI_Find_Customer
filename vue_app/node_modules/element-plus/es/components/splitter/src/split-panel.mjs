import { buildProps } from '../../../utils/vue/props/runtime.mjs';

const splitterPanelProps = buildProps({
  min: {
    type: [String, Number]
  },
  max: {
    type: [String, Number]
  },
  size: {
    type: [String, Number]
  },
  resizable: {
    type: Boolean,
    default: true
  },
  collapsible: Boolean
});

export { splitterPanelProps };
//# sourceMappingURL=split-panel.mjs.map
