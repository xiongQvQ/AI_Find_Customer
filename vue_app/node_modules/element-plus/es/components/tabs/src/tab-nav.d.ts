import type { ExtractPropTypes, __ExtractPublicPropTypes } from 'vue';
import type { TabBarInstance } from './tab-bar';
import type { TabPaneName, TabsPaneContext } from './constants';
export declare const tabNavProps: {
    readonly panes: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => {
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
        paneName: TabPaneName | undefined;
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
        paneName: TabPaneName | undefined;
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
        paneName: TabPaneName | undefined;
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
        paneName: TabPaneName | undefined;
        active: boolean;
        index: string | undefined;
        isClosable: boolean;
        isFocusInsidePane: () => boolean | undefined;
    }[]))[], unknown, unknown, () => [], boolean>;
    readonly currentName: import("element-plus/es/utils").EpPropFinalized<readonly [StringConstructor, NumberConstructor], unknown, unknown, "", boolean>;
    readonly editable: BooleanConstructor;
    readonly type: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "" | "card" | "border-card", unknown, "", boolean>;
    readonly stretch: BooleanConstructor;
};
export declare const tabNavEmits: {
    tabClick: (tab: TabsPaneContext, tabName: TabPaneName, ev: Event) => boolean;
    tabRemove: (tab: TabsPaneContext, ev: Event) => boolean;
};
export type TabNavProps = ExtractPropTypes<typeof tabNavProps>;
export type TabNavPropsPublic = __ExtractPublicPropTypes<typeof tabNavProps>;
export type TabNavEmits = typeof tabNavEmits;
declare const TabNav: import("vue").DefineComponent<{
    readonly panes: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => {
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
        paneName: TabPaneName | undefined;
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
        paneName: TabPaneName | undefined;
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
        paneName: TabPaneName | undefined;
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
        paneName: TabPaneName | undefined;
        active: boolean;
        index: string | undefined;
        isClosable: boolean;
        isFocusInsidePane: () => boolean | undefined;
    }[]))[], unknown, unknown, () => [], boolean>;
    readonly currentName: import("element-plus/es/utils").EpPropFinalized<readonly [StringConstructor, NumberConstructor], unknown, unknown, "", boolean>;
    readonly editable: BooleanConstructor;
    readonly type: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "" | "card" | "border-card", unknown, "", boolean>;
    readonly stretch: BooleanConstructor;
}, () => JSX.Element, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {
    tabClick: (tab: TabsPaneContext, tabName: TabPaneName, ev: Event) => boolean;
    tabRemove: (tab: TabsPaneContext, ev: Event) => boolean;
}, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<ExtractPropTypes<{
    readonly panes: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => {
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
        paneName: TabPaneName | undefined;
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
        paneName: TabPaneName | undefined;
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
        paneName: TabPaneName | undefined;
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
        paneName: TabPaneName | undefined;
        active: boolean;
        index: string | undefined;
        isClosable: boolean;
        isFocusInsidePane: () => boolean | undefined;
    }[]))[], unknown, unknown, () => [], boolean>;
    readonly currentName: import("element-plus/es/utils").EpPropFinalized<readonly [StringConstructor, NumberConstructor], unknown, unknown, "", boolean>;
    readonly editable: BooleanConstructor;
    readonly type: import("element-plus/es/utils").EpPropFinalized<StringConstructor, "" | "card" | "border-card", unknown, "", boolean>;
    readonly stretch: BooleanConstructor;
}>> & {
    onTabClick?: ((tab: {
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
        paneName: TabPaneName | undefined;
        active: boolean;
        index: string | undefined;
        isClosable: boolean;
        isFocusInsidePane: () => boolean | undefined;
    }, tabName: TabPaneName, ev: Event) => any) | undefined;
    onTabRemove?: ((tab: {
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
        paneName: TabPaneName | undefined;
        active: boolean;
        index: string | undefined;
        isClosable: boolean;
        isFocusInsidePane: () => boolean | undefined;
    }, ev: Event) => any) | undefined;
}, {
    readonly stretch: boolean;
    readonly type: import("element-plus/es/utils").EpPropMergeType<StringConstructor, "" | "card" | "border-card", unknown>;
    readonly editable: boolean;
    readonly panes: {
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
        paneName: TabPaneName | undefined;
        active: boolean;
        index: string | undefined;
        isClosable: boolean;
        isFocusInsidePane: () => boolean | undefined;
    }[];
    readonly currentName: import("element-plus/es/utils").EpPropMergeType<readonly [StringConstructor, NumberConstructor], unknown, unknown>;
}>;
export type TabNavInstance = InstanceType<typeof TabNav> & {
    scrollToActiveTab: () => Promise<void>;
    removeFocus: () => void;
    focusActiveTab: () => void;
    scheduleRender: () => void;
    tabListRef: HTMLDivElement | undefined;
    tabBarRef: TabBarInstance | undefined;
};
export default TabNav;
