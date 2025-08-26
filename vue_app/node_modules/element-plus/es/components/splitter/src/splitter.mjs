import { buildProps } from '../../../utils/vue/props/runtime.mjs';

const splitterProps = buildProps({
  layout: {
    type: String,
    default: "horizontal",
    values: ["horizontal", "vertical"]
  },
  lazy: Boolean
});

export { splitterProps };
//# sourceMappingURL=splitter.mjs.map
