import React, { useState, useEffect } from "react";
import proofTree from "./proof_tree.json";
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
  const [currentNode, setCurrentNode] = useState<TreeNode>(proofTree.tree); // Adjusted to access the tree property
  const [path, setPath] = useState<TreeNode[]>([proofTree.tree]); // Adjusted to access the tree property

  useEffect(() => {
    fetch("proof_tree.json")
      .then((response) => response.json())
      .then((data) => {
        const preprocessTree = (node: TreeNode) => {
          if (node.eval_score === "Infinity") {
            node.eval_score = Infinity;
          } else if (node.eval_score === "-Infinity") {
            node.eval_score = -Infinity;
          }
          node.children.forEach((child) => preprocessTree(child));
        };

        preprocessTree(data.tree); // Preprocess the tree to handle Infinity values
        setCurrentNode(data.tree);
        setPath([data.tree]);
      })
      .catch((error) => console.error("Failed to load proof tree:", error));
  }, []);

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
      <Box display="flex" p={5}>
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
      </Box>
    </ChakraProvider>
  );
};
