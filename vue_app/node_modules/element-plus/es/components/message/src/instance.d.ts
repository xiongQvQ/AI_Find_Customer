import type { ComponentInternalInstance, VNode } from 'vue';
import type { Mutable } from 'element-plus/es/utils';
import type { MessageHandler, MessagePlacement, MessageProps } from './message';
export type MessageContext = {
    id: string;
    vnode: VNode;
    handler: MessageHandler;
    vm: ComponentInternalInstance;
    props: Mutable<MessageProps>;
};
export declare const placementInstances: import("vue").ShallowReactive<Record<"top" | "bottom" | "top-left" | "top-right" | "bottom-left" | "bottom-right", MessageContext[]>>;
export declare const getOrCreatePlacementInstances: (placement: MessagePlacement) => MessageContext[];
export declare const getInstance: (id: string, placement: MessagePlacement) => {
    current: MessageContext;
    prev: MessageContext | undefined;
};
export declare const getLastOffset: (id: string, placement: MessagePlacement) => number;
export declare const getOffsetOrSpace: (id: string, offset: number, placement: MessagePlacement) => number;
