import { buildProps } from '../../../utils/vue/props/runtime.mjs';
import { iconPropType } from '../../../utils/vue/icon.mjs';

const dialogContentProps = buildProps({
  center: Boolean,
  alignCenter: {
    type: Boolean,
    default: void 0
  },
  closeIcon: {
    type: iconPropType
  },
  draggable: {
    type: Boolean,
    default: void 0
  },
  overflow: {
    type: Boolean,
    default: void 0
  },
  fullscreen: Boolean,
  headerClass: String,
  bodyClass: String,
  footerClass: String,
  showClose: {
    type: Boolean,
    default: true
  },
  title: {
    type: String,
    default: ""
  },
  ariaLevel: {
    type: String,
    default: "2"
  }
});
const dialogContentEmits = {
  close: () => true
};

export { dialogContentEmits, dialogContentProps };
//# sourceMappingURL=dialog-content.mjs.map
