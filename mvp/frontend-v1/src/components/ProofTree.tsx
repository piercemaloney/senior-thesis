import { useState, FC } from "react";
import { Box, IconButton, Flex, Stack, Button } from "@chakra-ui/react";
import { ChevronDownIcon, ChevronRightIcon } from "@chakra-ui/icons";
import { generateFromPath } from "../api";

// Define the structure of a tree node
interface TreeNodeProps {
  node: {
    id: number;
    label: string;
    path?: string[]; // Does not include self
    children?: TreeNodeProps["node"][];
  };
}

const TreeNode: FC<TreeNodeProps> = ({ node }) => {
  const [isCollapsed, setIsCollapsed] = useState(true);
  const toggleCollapse = () => setIsCollapsed(!isCollapsed);

  const handleGenerate = async () => {
    const fullPath = node.path ? [...node.path, node.label] : [node.label];
    console.log(fullPath);
    const nextTactics = await generateFromPath(fullPath);
    console.log(nextTactics);
    // nextTactics is of the form ["tactic1", "tactic2", ...]
    const newChildren = nextTactics.map((tactic: string, index: number) => ({
      id: index,
      label: tactic,
    }));
    // Update the node with new children here
  };

  return (
    <Box border="1px" borderColor="gray.200" p={4} m={2}>
      {node.children ? (
        <IconButton
          aria-label="Toggle Collapse"
          icon={isCollapsed ? <ChevronRightIcon /> : <ChevronDownIcon />}
          onClick={toggleCollapse}
          size="sm"
        />
      ) : (
        <Button onClick={handleGenerate} size="sm">
          {node.label}
        </Button>
      )}
      {node.children && node.label}
      {!isCollapsed && node.children && (
        <Stack direction="row" spacing={5} align="center">
          {node.children.map((child) => (
            <Box key={child.id}>
              <TreeNode node={child} />
            </Box>
          ))}
        </Stack>
      )}
    </Box>
  );
};

interface ProofTreeProps {
  data: TreeNodeProps["node"];
}

const ProofTree: FC<ProofTreeProps> = ({ data }) => {
  return <TreeNode node={data} />;
};

export default ProofTree;
