import React, { useState } from "react";
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

interface TreeNode {
  text: string;
  proofState: string;
  children: TreeNode[];
}

// Example binary tree node structure
const proofTree = {
  text: "Theorem zero_plus_n_equals_n : forall n : nat, 0 + n = n.",
  proofState: "forall n : nat, 0 + n = n",
  children: [
    {
      text: "Proof.",
      proofState:
        "forall n : nat, 0 + n = n",
      children: [
        {
          text: "intro n.",
          proofState:
            "n: nat\n0 + n = n",
          children: [
            {
            text: "simpl.",
            proofState: "No more goals.",
            children: [],
          }],
        },
        {
          text: "simpl.",
          proofState: "No more goals.",
          children: [
          ],
        },
      ],
    },
  ],
};

export const App = () => {
  const [currentNode, setCurrentNode] = useState<TreeNode>(proofTree);
  const [path, setPath] = useState<TreeNode[]>([proofTree]); // Initialize with root node in path

  const handleOptionClick = (childNode: TreeNode, level: number) => {
    setCurrentNode(childNode);
    setPath((prevPath) => {
      // Check if the clicked node is already in the path (indicating a step back)
      const existingIndex = prevPath.findIndex(node => node.text === childNode.text);
      if (existingIndex !== -1) {
        // If stepping back, trim the path to that point
        return prevPath.slice(0, existingIndex + 1);
      } else {
        // Otherwise, append the new node to the path
        return [...prevPath.slice(0, level + 1), childNode];
      }
    });
  };

  const renderOptions = (node: TreeNode, level: number) => {
    // Render options for all nodes, allowing to step back in the path
    return node.children.map((child, index) => (
      <Button key={index} onClick={() => handleOptionClick(child, level)} m={1}>
        {child.text}
      </Button>
    ));
  };

  const renderProofPath = () => {
    // Render each node in the path, including the proof state in a new column
    return path.map((node, index) => (
      <Tr key={index}>
        <Td>{node.text}</Td>
        <Td>{renderOptions(node, index)}</Td>
        <Td>{node.proofState}</Td> 
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
              <Th>Options</Th>
              <Th>Proof State</Th> 
            </Tr>
          </Thead>
          <Tbody>{renderProofPath()}</Tbody>
        </Table>
      </Box>
    </ChakraProvider>
  );
};


// import React, { useState } from "react";
// import {
//   ChakraProvider,
//   Box,
//   Button,
//   Table,
//   Thead,
//   Tbody,
//   Tr,
//   Th,
//   Td,
//   theme,
// } from "@chakra-ui/react";

// // Assuming proofTree is defined as in your context

// export const App = () => {
//   const [currentNode, setCurrentNode] = useState(proofTree);
//   const [path, setPath] = useState([proofTree]); // Initialize with root node in path

//   const handleOptionClick = (childNode) => {
//     setCurrentNode(childNode);
//     setPath((prevPath) => [...prevPath, childNode]); // Add the child node to the path
//   };

//   const renderOptions = (node) => {
//     // Only render options for the last node in the path
//     if (node === path[path.length - 1]) {
//       return node.children.map((child, index) => (
//         <Button key={index} onClick={() => handleOptionClick(child)} m={1}>
//           Option {index + 1}
//         </Button>
//       ));
//     }
//     return null;
//   };

//   const renderProofPath = () => {
//     // Render each node in the path
//     return path.map((node, index) => (
//       <Tr key={index}>
//         <Td>{node.text}</Td>
//         <Td>{renderOptions(node)}</Td>
//       </Tr>
//     ));
//   };

//   return (
//     <ChakraProvider theme={theme}>
//       <Box display="flex" p={5}>
//         <Table variant="simple">
//           <Thead>
//             <Tr>
//               <Th>Proof Text</Th>
//               <Th>Options</Th>
//             </Tr>
//           </Thead>
//           <Tbody>{renderProofPath()}</Tbody>
//         </Table>
//       </Box>
//     </ChakraProvider>
//   );
// };