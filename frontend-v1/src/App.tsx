import * as React from "react";
import { ChakraProvider, Box, theme } from "@chakra-ui/react";
import { ColorModeSwitcher } from "./ColorModeSwitcher";

import ProofTree from "./components/ProofTree"; // Adjust the import path as needed

// Sample data for the proof tree
const sampleData = {
  id: 0,
  label: "Root Node",
  children: [
    {
      id: 0,
      label: "Child Node 1",
      children: [
        {
          id: 0,
          label: "Grandchild Node 1",
        },
        {
          id: 1,
          label: "Grandchild Node 2",
        },
        {
          id: 2,
          label: "Grandchild Node 3",
          children: [
            {
              id: 0,
              label: "Great Grandchild Node 1",
            },
            {
              id: 1,
              label: "Great Grandchild Node 2",
            },
          ],
        },
      ],
    },
    {
      id: 1,
      label: "Child Node 2",
    },
  ],
};

export const App = () => (
  <ChakraProvider theme={theme}>
    <Box textAlign="center" fontSize="xl">
      <ProofTree data={sampleData} />
    </Box>
  </ChakraProvider>
);
