import type { ComponentInternalInstance, VNode } from 'vue';
type ChildEssential = {
    uid: number;
    getVnode: () => VNode;
};
export declare const useOrderedChildren: <T extends ChildEssential>(vm: ComponentInternalInstance, childComponentName: string) => {
    children: import("vue").ShallowRef<T[]>;
    addChild: (child: T) => void;
    removeChild: (child: T) => void;
    ChildrenSorter: import("vue").DefineComponent<{}, () => VNode<import("vue").RendererNode, import("vue").RendererElement, {
        [key: string]: any;
    }> | null, {}, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, import("vue").EmitsOptions, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{}>>, {}>;
};
export {};
