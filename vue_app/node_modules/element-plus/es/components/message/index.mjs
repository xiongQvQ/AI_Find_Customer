import message from './src/method.mjs';
export { MESSAGE_DEFAULT_PLACEMENT, messageDefaults, messageEmits, messagePlacement, messageProps, messageTypes } from './src/message2.mjs';
import { withInstallFunction } from '../../utils/vue/install.mjs';

const ElMessage = withInstallFunction(message, "$message");

export { ElMessage, ElMessage as default };
//# sourceMappingURL=index.mjs.map
