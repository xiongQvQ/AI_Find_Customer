import type { SelectV2Props } from './token';
import type { Option, SelectStates } from './select.types';
export declare function useAllowCreate(props: SelectV2Props, states: SelectStates): {
    createNewOption: (query: string) => void;
    removeNewOption: (option: Option) => void;
    selectNewOption: (option: Option) => void;
    clearAllNewOption: () => void;
};
