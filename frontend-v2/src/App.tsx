import React, { useState, useEffect, ChangeEvent } from "react";
import {
  ChakraProvider,
  Box,
  Button,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  theme,
  Input,
} from "@chakra-ui/react";

// Updated TreeNode interface to reflect fg_goals as an array of strings
interface TreeNode {
  tactic: string;
  fg_goals: string[];
  bg_goals: string[]; // Assuming this is added to the TreeNode interface
  children: TreeNode[];
  eval_score: number | string;
}

export const App = () => {
  const [currentNode, setCurrentNode] = useState<TreeNode | null>(null); // Adjusted to access the tree property
  const [path, setPath] = useState<TreeNode[]>([]); // Adjusted to access the tree property

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files ? event.target.files[0] : null;
    if (!file) {
      return;
    }

    const reader = new FileReader();
  reader.onload = (e) => {
    let text = e.target?.result as string;
    // Replace specific values in the text content here before parsing
    text = text.replace(/"eval_score":\s*Infinity\b/g, '"eval_score": "100000000"');
    text = text.replace(/"eval_score":\s*Infinity\b/g, '"eval_score": "-100000000"');
    
    try {
      const data = JSON.parse(text);
      preprocessTree(data.tree); // Assuming your JSON structure has a "tree" property
      setCurrentNode(data.tree);
      setPath([data.tree]);
    } catch (error) {
      console.error("Error parsing JSON:", error);
    }
  };
  reader.readAsText(file);
};

  const preprocessTree = (node: TreeNode) => {
    if (node.eval_score === "Infinity") {
      node.eval_score = Infinity;
    } else if (node.eval_score === "-Infinity") {
      node.eval_score = -Infinity;
    }
    node.children.forEach((child) => preprocessTree(child));
  };

  const handleOptionClick = (childNode: TreeNode, level: number) => {
    setCurrentNode(childNode);
    setPath((prevPath) => {
      const existingIndex = prevPath.findIndex(
        (node) => node.tactic === childNode.tactic
      );
      if (existingIndex !== -1) {
        return prevPath.slice(0, existingIndex + 1);
      } else {
        return [...prevPath.slice(0, level + 1), childNode];
      }
    });
  };

  const renderOptions = (node: TreeNode, level: number) => {
    return node.children.map((child, index) => (
      <Button key={index} onClick={() => handleOptionClick(child, level)} m={1}>
        {child.tactic}
      </Button>
    ));
  };

  const renderProofPath = () => {
    return path.map((node, index) => (
      <Tr key={index}>
        <Td>{node.tactic}</Td>
        <Td>{renderOptions(node, index)}</Td>
        <Td>
          {node.fg_goals.length > 0 ? (
            node.fg_goals.join(", ")
          ) : node.bg_goals.length > 0 ? (
            <>
              <i>BG Goals</i>: {node.bg_goals.join(", ")}
            </>
          ) : (
            "No goals remaining."
          )}
        </Td>
      </Tr>
    ));
  };

  return (
    <ChakraProvider theme={theme}>
      <Box display="flex" flexDirection="column" p={5}>
        <Input type="file" onChange={handleFileChange} accept=".json" />
        {currentNode && (
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th>Proof Text</Th>
                <Th>Tactic Options</Th>
                <Th>Proof State</Th>
              </Tr>
            </Thead>
            <Tbody>{renderProofPath()}</Tbody>
          </Table>
        )}
      </Box>
    </ChakraProvider>
  );
};