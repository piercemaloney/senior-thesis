import React, { useState, useEffect } from "react";
import { Box, Button, Text, Spinner, Flex, Textarea } from "@chakra-ui/react";
import { motion } from "framer-motion";
import { vote, generate } from "../api";

const MotionButton = motion(Button);

const ProofComponent: React.FC = () => {
  const initialText = `Lemma mult_is_zero : forall n m : nat, n * m = 0 <-> n = 0 \/ m = 0.
Proof.
  intros n m.
  split.
  - (* Forward direction: n * m = 0 implies n = 0 \/ m = 0 *)
    intros H.`;

  const [currentProof, setCurrentProof] = useState(initialText);
  const [state, setState] = useState<"generating" | "continuing">("generating");
  const [nodes, setNodes] = useState<[string, string] | null>(null);
  const [loading, setLoading] = useState(false);
  const [proofBegan, setProofBegan] = useState(false);
  const [enlargedNode, setEnlargedNode] = useState<string | null>(null);

  const generateIdeas = async () => {
    setLoading(true);
    const response = await generate(currentProof);
    setNodes(response);
    setLoading(false);
    // setState("continuing");
  };

  const continueProof = async () => {
    setLoading(true);
    if (!nodes || nodes.length != 2) {
      throw new Error("Invalid nodes");
    }
    const response = await vote(currentProof, nodes);
    const selectedNode = nodes[response.index];
    setEnlargedNode(selectedNode);
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setCurrentProof((prevProof) => prevProof + `\n${selectedNode}`);
    setNodes(null);
    setLoading(false);
    // setState("generating");
  };

  useEffect(() => {
    if (proofBegan) {
      if (state === "generating") {
        generateIdeas();
      } else if (state === "continuing") {
        continueProof();
      }
    }
  }, [state, proofBegan]);

  const beginProof = async () => {
    setProofBegan(true);
  };

  const buttonVariants = {
    initial: { opacity: 1, x: 0 },
    selected: { opacity: 1, x: 0, scale: 1.25, transition: { duration: 0.5 } },
    unselected: { opacity: 0.25, x: 0, transition: { duration: 0.5 } },
  };

  return (
    <Flex direction="column" justifyContent="center" alignItems="center" p={5}>
      {!proofBegan ? (
        <>
          <Box mb={4}>
            <Textarea
              defaultValue={initialText}
              isReadOnly
              size="sm"
              minW="500px"
              resize="vertical"
            />
          </Box>
          <Button onClick={beginProof}>Begin</Button>
        </>
      ) : (
        <>
          <Text>
            {currentProof.split("\n").map((line, i) => (
              <React.Fragment key={i}>
                {line}
                <br />
              </React.Fragment>
            ))}
          </Text>
          {nodes && (
            <Flex direction="column" justify="space-between" mt={4}>
              <Flex direction="row" justify="space-between" mb={4}>
                {nodes.map((node, idx) => (
                  <Box key={idx}>
                    <MotionButton
                      mx={2}
                      variants={buttonVariants}
                      initial="initialLoad"
                      animate={
                        enlargedNode === null
                          ? "initialLoad"
                          : enlargedNode === node
                          ? "selected"
                          : "initialLoad"
                      }
                    >
                      {node}
                    </MotionButton>
                  </Box>
                ))}
              </Flex>
              <Button size="sm" onClick={() => setState("continuing")}>
                Continue
              </Button>
            </Flex>
          )}
          {state === "continuing" && !loading && (
            <Button onClick={() => setState("generating")}>Generate</Button>
          )}
          {loading && (
            <Flex justify="center" mt={4}>
              <Spinner size="xl" />
            </Flex>
          )}
        </>
      )}
    </Flex>
  );
};

export default ProofComponent;
