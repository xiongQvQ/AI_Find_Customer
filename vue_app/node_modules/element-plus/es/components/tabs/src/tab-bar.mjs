import { buildProps, definePropType } from '../../../utils/vue/props/runtime.mjs';
import { mutable } from '../../../utils/typescript.mjs';

const tabBarProps = buildProps({
  tabs: {
    type: definePropType(Array),
    default: () => mutable([])
  },
  tabRefs: {
    type: definePropType(Object),
    default: () => mutable({})
  }
});

export { tabBarProps };
//# sourceMappingURL=tab-bar.mjs.map
