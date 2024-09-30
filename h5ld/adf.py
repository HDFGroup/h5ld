import typing
import io
import numpy as np
import h5py
from rdflib import ConjunctiveGraph
from rdflib.namespace import NamespaceManager


class AllotropeDF:
    """Allotrope Data Format <https://docs.allotrope.org/Allotrope%20Data%20Format.html>."""

    name = "Allotrope Data Format"
    short_name = "ADF"

    @staticmethod
    def verify_format(f: h5py.File) -> bool:
        """Check if the HDF5 file is an ADF file."""
        try:
            # f.attrs['adf-file-id']
            f.attrs["adf-lib-version"]
            f.attrs["adf-version"]
            return True
        except Exception:
            return False

    @staticmethod
    def check_ld(f: h5py.File, report: bool = False) -> bool:
        """Check if ADF file has useable data description content."""
        try:
            quads = f["/data-description/quads"]
            assert quads.dtype.name == "int64"
            assert len(quads.shape) == 2
            assert quads.shape[1] == 5
            f["/data-description/dictionary/keys"]
            f["/data-description/dictionary/bytes"]
            if report:
                print(f'Number of RDF quads: {quads.attrs["size"]}')
            return True
        except Exception:
            return False

    def __init__(self, f: h5py.File) -> None:
        self._h5f = f

    def _get_string(self, key: np.int64) -> str:
        value = self.key_store[key, :]
        if value[-1] > 0:
            return value[: value[-1]].tobytes().decode("utf-8")
        else:
            start = np.frombuffer(value[:8], dtype=">i8")[0]
            count = np.frombuffer(value[8:-1], dtype=">i4")[0]
            return self.str_store[start : start + count].decode("utf-8")  # noqa: E203

    def _resource_node(self, res_key: np.int64, val_key: np.int64) -> str:
        """Form an IRI RDF node string."""
        val = self._get_string(val_key)
        res = self._get_string(res_key)
        return f"<{res}{val}>"

    def _literal_node(self, res_key: np.int64, val_key: np.int64) -> str:
        """Form a literal RDF node string."""
        val = self._get_string(val_key)
        val = (
            val.replace('"', r"\"")
            .replace("'", r"\'")
            .replace("\t", r"\t")
            .replace("\n", r"\n")
            .replace("\r", r"\r")
            .replace("\b", r"\b")
            .replace("\f", r"\f")
        )
        if res_key == 0:
            # This is an assumption to be validated...
            return f'"{val}"'
        else:
            res = self._get_string(res_key)
            return f'"{val}"^^<{res}>'

    def _blank_node(self, res_key: np.int64, val_key: np.int64) -> str:
        """Form a blank RDF node string."""
        val = self._get_string(val_key)
        if val[0] == "-":
            val = val[1:]
        return f"_:{val}"

    def _get_quads(self, store: io.TextIOWrapper) -> None:
        """Read quads from the ADF file."""
        quads = self._h5f["/data-description/quads"]
        num_quads = quads.shape[0]
        num_good_quads = quads.attrs["size"]
        quads = quads[...]
        quads = quads[quads[:, -1] == 0, :-1]
        self.key_store = self._h5f["/data-description/dictionary/keys"][...]
        self.str_store = self._h5f["/data-description/dictionary/bytes"][...].tobytes()

        node_id_31bit_mask = 0x7FFFFFFF
        template = [self._blank_node, self._resource_node, self._literal_node]

        for qrow in range(num_quads):
            if qrow >= num_good_quads:
                break

            quad_content = list()
            quad = quads[qrow, :]

            node_value_key = np.bitwise_and(quad, node_id_31bit_mask)
            node_key = np.bitwise_and(
                np.right_shift(quad, 31, out=quad), node_id_31bit_mask
            )
            node_kind = np.bitwise_and(np.right_shift(quad, 31), 3)

            for i in range(node_kind.size):
                quad_content.append(
                    template[node_kind[i]](
                        res_key=node_key[i], val_key=node_value_key[i]
                    )
                )
            store.write(" ".join(quad_content[1:]) + f" {quad_content[0]}" + " .\n")

    def dump_ld(
        self,
        destination: typing.Optional[typing.Union[str, io.BytesIO]] = None,
        format: typing.Optional[str] = None,
    ) -> typing.Optional[ConjunctiveGraph]:
        """Dump ADF Data Description content to destination in requested format."""
        buf = io.BytesIO()
        store = io.TextIOWrapper(buf, encoding="utf-8")
        self._get_quads(store)
        store.flush()
        buf.seek(0, io.SEEK_SET)
        g = ConjunctiveGraph()
        nsmgr = NamespaceManager(g)
        for pre, iri in self.namespaces.items():
            nsmgr.bind(pre, iri)
        if destination:
            if format == "nquads":
                if isinstance(destination, str):
                    destination = open(destination, mode="wb")
                destination.write(buf.getvalue())
            else:
                g.parse(source=buf, format="nquads")
                if format == "json-ld":
                    g.serialize(
                        destination=destination, format=format, context=self.namespaces
                    )
                else:
                    g.serialize(destination=destination, format=format)
        else:
            g.parse(source=buf, format="nquads")
            return g

    def get_ld(self) -> ConjunctiveGraph:
        """Get ADF data description content as an rdflib.ConjunctiveGraph object."""
        return self.dump_ld(destination=None)

    @property
    def namespaces(self) -> dict[str, str]:
        """ADF namespace prefixes."""
        return {
            "hdf5": "http://purl.allotrope.org/ontologies/hdf5/1.8#",
            "afs-hdf5": "http://purl.allotrope.org/shapes/hdf#",
            "adf-dc-hdf5": "http://purl.allotrope.org/ontologies/datacube-hdf-map#",
            "adf-dp": "http://purl.allotrope.org/ontologies/datapackage#",
            "adf-dd": "http://purl.allotrope.org/ontologies/datadescription#",
            "adf-dc": "http://purl.allotrope.org/ontologies/datacube#",
            "af-sh": "http://purl.allotrope.org/ontologies/shapes/",
            "af-c": "http://purl.allotrope.org/ontologies/common#",
            "af-e": "http://purl.allotrope.org/ontologies/equipment#",
            "af-m": "http://purl.allotrope.org/ontologies/material#",
            "af-p": "http://purl.allotrope.org/ontologies/process#",
            "af-q": "http://purl.allotrope.org/ontologies/quality#",
            "af-r": "http://purl.allotrope.org/ontologies/result#",
            "af-s": "http://purl.allotrope.org/shape/",
            "af-x": "http://purl.allotrope.org/ontologies/property#",
            "af-a": "http://purl.allotrope.org/ontologies/audit#",
            "sh": "http://www.w3.org/ns/shacl#",
            "qb": "http://purl.org/linked-data/cube#",
            "qudt": "http://qudt.org/schema/qudt#",
            "qudt-unit": "http://qudt.org/vocab/unit#",
            "qudt-quantity": "http://qudt.org/vocab/quantity#",
            "dct": "http://purl.org/dc/terms/",
            "skos": "http://www.w3.org/2004/02/skos/core#",
            "owl": "http://www.w3.org/2002/07/owl#",
            "xsd": "http://www.w3.org/2001/XMLSchema#",
            "pav": "http://purl.org/pav/",
            "obo": "http://purl.obolibrary.org/obo/",
        }
