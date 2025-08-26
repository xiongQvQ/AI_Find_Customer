import { isVNode, render, createVNode } from 'vue';
import MessageConstructor from './message.mjs';
import { messageTypes, MESSAGE_DEFAULT_PLACEMENT, messageDefaults, messagePlacement } from './message2.mjs';
import { getOrCreatePlacementInstances, placementInstances } from './instance.mjs';
import { messageConfig } from '../../config-provider/src/config-provider.mjs';
import { isClient } from '@vueuse/core';
import { isNumber, isBoolean, isElement } from '../../../utils/types.mjs';
import { hasOwn, isString, isFunction } from '@vue/shared';
import { debugWarn } from '../../../utils/error.mjs';

let seed = 1;
const normalizeAppendTo = (normalized) => {
  const appendTo = normalized.appendTo;
  if (!appendTo) {
    normalized.appendTo = document.body;
  } else if (isString(normalized.appendTo)) {
    let appendTo2 = document.querySelector(normalized.appendTo);
    if (!isElement(appendTo2)) {
      appendTo2 = document.body;
    }
    normalized.appendTo = appendTo2;
  }
};
const normalizePlacement = (normalized) => {
  if (!normalized.placement && isString(messageConfig.placement) && messageConfig.placement) {
    normalized.placement = messageConfig.placement;
  }
  if (!normalized.placement) {
    normalized.placement = MESSAGE_DEFAULT_PLACEMENT;
  }
  if (!messagePlacement.includes(normalized.placement)) {
    debugWarn("ElMessage", `Invalid placement: ${normalized.placement}. Falling back to '${MESSAGE_DEFAULT_PLACEMENT}'.`);
    normalized.placement = MESSAGE_DEFAULT_PLACEMENT;
  }
};
const normalizeOptions = (params) => {
  const options = !params || isString(params) || isVNode(params) || isFunction(params) ? { message: params } : params;
  const normalized = {
    ...messageDefaults,
    ...options
  };
  normalizeAppendTo(normalized);
  normalizePlacement(normalized);
  if (isBoolean(messageConfig.grouping) && !normalized.grouping) {
    normalized.grouping = messageConfig.grouping;
  }
  if (isNumber(messageConfig.duration) && normalized.duration === 3e3) {
    normalized.duration = messageConfig.duration;
  }
  if (isNumber(messageConfig.offset) && normalized.offset === 16) {
    normalized.offset = messageConfig.offset;
  }
  if (isBoolean(messageConfig.showClose) && !normalized.showClose) {
    normalized.showClose = messageConfig.showClose;
  }
  if (isBoolean(messageConfig.plain) && !normalized.plain) {
    normalized.plain = messageConfig.plain;
  }
  return normalized;
};
const closeMessage = (instance) => {
  const placement = instance.props.placement || MESSAGE_DEFAULT_PLACEMENT;
  const instances = placementInstances[placement];
  const idx = instances.indexOf(instance);
  if (idx === -1)
    return;
  instances.splice(idx, 1);
  const { handler } = instance;
  handler.close();
};
const createMessage = ({ appendTo, ...options }, context) => {
  const id = `message_${seed++}`;
  const userOnClose = options.onClose;
  const container = document.createElement("div");
  const props = {
    ...options,
    id,
    onClose: () => {
      userOnClose == null ? void 0 : userOnClose();
      closeMessage(instance);
    },
    onDestroy: () => {
      render(null, container);
    }
  };
  const vnode = createVNode(MessageConstructor, props, isFunction(props.message) || isVNode(props.message) ? {
    default: isFunction(props.message) ? props.message : () => props.message
  } : null);
  vnode.appContext = context || message._context;
  render(vnode, container);
  appendTo.appendChild(container.firstElementChild);
  const vm = vnode.component;
  const handler = {
    close: () => {
      vm.exposed.close();
    }
  };
  const instance = {
    id,
    vnode,
    vm,
    handler,
    props: vnode.component.props
  };
  return instance;
};
const message = (options = {}, context) => {
  if (!isClient)
    return { close: () => void 0 };
  const normalized = normalizeOptions(options);
  const instances = getOrCreatePlacementInstances(normalized.placement || MESSAGE_DEFAULT_PLACEMENT);
  if (normalized.grouping && instances.length) {
    const instance2 = instances.find(({ vnode: vm }) => {
      var _a;
      return ((_a = vm.props) == null ? void 0 : _a.message) === normalized.message;
    });
    if (instance2) {
      instance2.props.repeatNum += 1;
      instance2.props.type = normalized.type;
      return instance2.handler;
    }
  }
  if (isNumber(messageConfig.max) && instances.length >= messageConfig.max) {
    return { close: () => void 0 };
  }
  const instance = createMessage(normalized, context);
  instances.push(instance);
  return instance.handler;
};
messageTypes.forEach((type) => {
  message[type] = (options = {}, appContext) => {
    const normalized = normalizeOptions(options);
    return message({ ...normalized, type }, appContext);
  };
});
function closeAll(type) {
  for (const placement in placementInstances) {
    if (hasOwn(placementInstances, placement)) {
      const instances = [...placementInstances[placement]];
      for (const instance of instances) {
        if (!type || type === instance.props.type) {
          instance.handler.close();
        }
      }
    }
  }
}
function closeAllByPlacement(placement) {
  if (!placementInstances[placement])
    return;
  const instances = [...placementInstances[placement]];
  instances.forEach((instance) => instance.handler.close());
}
message.closeAll = closeAll;
message.closeAllByPlacement = closeAllByPlacement;
message._context = null;

export { closeAll, closeAllByPlacement, message as default };
//# sourceMappingURL=method.mjs.map
