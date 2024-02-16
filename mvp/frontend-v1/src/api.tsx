import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
});

const generateFromPath = async (path: string[]) => {
  const current_proof = path.join("\n");
  console.log(current_proof);
  const response = await api.post("/generate", { current_proof });
  console.log(response.data);
  return response.data;
};

const generate = async (current_proof: string) => {
  const response = await api.post("/generate", { current_proof });
  return response.data;
};

const vote = async (current_proof: string, proposed_steps: string[]) => {
  const response = await api.post("/vote", { current_proof, proposed_steps });
  return response.data;
};

export default api;
export { generateFromPath };
