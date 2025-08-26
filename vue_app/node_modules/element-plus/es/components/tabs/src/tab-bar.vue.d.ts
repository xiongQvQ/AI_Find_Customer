import type { CSSProperties } from 'vue';
declare const _default: import("vue").DefineComponent<{
    readonly tabs: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => {
        uid: number;
        getVnode: () => import("vue").VNode;
        slots: import("vue").Slots;
        props: {
            readonly label: string;
            readonly disabled: boolean;
            readonly closable: boolean;
            readonly lazy: boolean;
            readonly name?: import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, NumberConstructor], unknown, unknown> | undefined;
        };
        paneName: import("./constants").TabPaneName | undefined;
        active: boolean;
        index: string | undefined;
        isClosable: boolean;
        isFocusInsidePane: () => boolean | undefined;
    }[]) | (() => {
        uid: number;
        getVnode: () => import("vue").VNode;
        slots: import("vue").Slots;
        props: {
            readonly label: string;
            readonly disabled: boolean;
            readonly closable: boolean;
            readonly lazy: boolean;
            readonly name?: import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, NumberConstructor], unknown, unknown> | undefined;
        };
        paneName: import("./constants").TabPaneName | undefined;
        active: boolean;
        index: string | undefined;
        isClosable: boolean;
        isFocusInsidePane: () => boolean | undefined;
    }[]) | ((new (...args: any[]) => {
        uid: number;
        getVnode: () => import("vue").VNode;
        slots: import("vue").Slots;
        props: {
            readonly label: string;
            readonly disabled: boolean;
            readonly closable: boolean;
            readonly lazy: boolean;
            readonly name?: import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, NumberConstructor], unknown, unknown> | undefined;
        };
        paneName: import("./constants").TabPaneName | undefined;
        active: boolean;
        index: string | undefined;
        isClosable: boolean;
        isFocusInsidePane: () => boolean | undefined;
    }[]) | (() => {
        uid: number;
        getVnode: () => import("vue").VNode;
        slots: import("vue").Slots;
        props: {
            readonly label: string;
            readonly disabled: boolean;
            readonly closable: boolean;
            readonly lazy: boolean;
            readonly name?: import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, NumberConstructor], unknown, unknown> | undefined;
        };
        paneName: import("./constants").TabPaneName | undefined;
        active: boolean;
        index: string | undefined;
        isClosable: boolean;
        isFocusInsidePane: () => boolean | undefined;
    }[]))[], unknown, unknown, () => [], boolean>;
    readonly tabRefs: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => {
        [key: string]: HTMLDivElement;
        [key: number]: HTMLDivElement;
    }) | (() => {
        [key: string]: HTMLDivElement;
        [key: number]: HTMLDivElement;
    }) | ((new (...args: any[]) => {
        [key: string]: HTMLDivElement;
        [key: number]: HTMLDivElement;
    }) | (() => {
        [key: string]: HTMLDivElement;
        [key: number]: HTMLDivElement;
    }))[], unknown, unknown, () => import("element-plus/es/utils").Mutable<{}>, boolean>;
}, {
    /** @description tab root html element */
    ref: import("vue").Ref<HTMLDivElement | undefined>;
    /** @description method to manually update tab bar style */
    update: () => CSSProperties;
}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, Record<string, any>, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{
    readonly tabs: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => {
        uid: number;
        getVnode: () => import("vue").VNode;
        slots: import("vue").Slots;
        props: {
            readonly label: string;
            readonly disabled: boolean;
            readonly closable: boolean;
            readonly lazy: boolean;
            readonly name?: import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, NumberConstructor], unknown, unknown> | undefined;
        };
        paneName: import("./constants").TabPaneName | undefined;
        active: boolean;
        index: string | undefined;
        isClosable: boolean;
        isFocusInsidePane: () => boolean | undefined;
    }[]) | (() => {
        uid: number;
        getVnode: () => import("vue").VNode;
        slots: import("vue").Slots;
        props: {
            readonly label: string;
            readonly disabled: boolean;
            readonly closable: boolean;
            readonly lazy: boolean;
            readonly name?: import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, NumberConstructor], unknown, unknown> | undefined;
        };
        paneName: import("./constants").TabPaneName | undefined;
        active: boolean;
        index: string | undefined;
        isClosable: boolean;
        isFocusInsidePane: () => boolean | undefined;
    }[]) | ((new (...args: any[]) => {
        uid: number;
        getVnode: () => import("vue").VNode;
        slots: import("vue").Slots;
        props: {
            readonly label: string;
            readonly disabled: boolean;
            readonly closable: boolean;
            readonly lazy: boolean;
            readonly name?: import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, NumberConstructor], unknown, unknown> | undefined;
        };
        paneName: import("./constants").TabPaneName | undefined;
        active: boolean;
        index: string | undefined;
        isClosable: boolean;
        isFocusInsidePane: () => boolean | undefined;
    }[]) | (() => {
        uid: number;
        getVnode: () => import("vue").VNode;
        slots: import("vue").Slots;
        props: {
            readonly label: string;
            readonly disabled: boolean;
            readonly closable: boolean;
            readonly lazy: boolean;
            readonly name?: import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, NumberConstructor], unknown, unknown> | undefined;
        };
        paneName: import("./constants").TabPaneName | undefined;
        active: boolean;
        index: string | undefined;
        isClosable: boolean;
        isFocusInsidePane: () => boolean | undefined;
    }[]))[], unknown, unknown, () => [], boolean>;
    readonly tabRefs: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => {
        [key: string]: HTMLDivElement;
        [key: number]: HTMLDivElement;
    }) | (() => {
        [key: string]: HTMLDivElement;
        [key: number]: HTMLDivElement;
    }) | ((new (...args: any[]) => {
        [key: string]: HTMLDivElement;
        [key: number]: HTMLDivElement;
    }) | (() => {
        [key: string]: HTMLDivElement;
        [key: number]: HTMLDivElement;
    }))[], unknown, unknown, () => import("element-plus/es/utils").Mutable<{}>, boolean>;
}>>, {
    readonly tabs: {
        uid: number;
        getVnode: () => import("vue").VNode;
        slots: import("vue").Slots;
        props: {
            readonly label: string;
            readonly disabled: boolean;
            readonly closable: boolean;
            readonly lazy: boolean;
            readonly name?: import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, NumberConstructor], unknown, unknown> | undefined;
        };
        paneName: import("./constants").TabPaneName | undefined;
        active: boolean;
        index: string | undefined;
        isClosable: boolean;
        isFocusInsidePane: () => boolean | undefined;
    }[];
    readonly tabRefs: {
        [key: string]: HTMLDivElement;
        [key: number]: HTMLDivElement;
    };
}>;
export default _default;
