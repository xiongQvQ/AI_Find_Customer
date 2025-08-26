import type Node from '../model/node';
interface Props {
    node?: Node;
    accordion: boolean;
}
export declare function useNodeExpandEventBroadcast(props: Props): {
    broadcastExpanded: (node?: Node) => void;
};
export {};
